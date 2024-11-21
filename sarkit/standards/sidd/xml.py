"""
========
SIDD XML
========

Functions from SIDD Volume 1 Design & Implementation Description Document.

"""

import numbers
import re
from collections.abc import Sequence
from typing import Any

import lxml.etree
import numpy as np
import numpy.typing as npt

import sarkit.standards.sicd.xml as sicdxml
import sarkit.standards.xml as ssxml


class AngleMagnitudeType(ssxml.ArrayType):
    """
    Transcoder for double-precision floating point angle magnitude XML parameter type.

    """

    def __init__(self, child_ns: str = "") -> None:
        super().__init__(
            subelements={c: ssxml.DblType() for c in ("Angle", "Magnitude")},
            child_ns=child_ns,
        )


class FilterCoefficientType(ssxml.Type):
    """
    Transcoder for FilterCoefficients.
    Attributes may either be (row, col) or (phasing, point)

    Parameters
    ----------
    attrib_type : str
        Attribute names, either "rowcol" or "phasingpoint"
    child_ns : str, optional
        Namespace to use for child elements.  Parent namespace used if unspecified.

    """

    def __init__(self, attrib_type: str, child_ns: str = "") -> None:
        if attrib_type == "rowcol":
            self.size_x_name = "numRows"
            self.size_y_name = "numCols"
            self.coef_x_name = "row"
            self.coef_y_name = "col"
        elif attrib_type == "phasingpoint":
            self.size_x_name = "numPhasings"
            self.size_y_name = "numPoints"
            self.coef_x_name = "phasing"
            self.coef_y_name = "point"
        else:
            raise ValueError(f"Unknown attrib_type of {attrib_type}")
        self.child_ns = child_ns

    def parse_elem(self, elem: lxml.etree.Element) -> npt.NDArray:
        """Returns an array of filter coefficients encoded in ``elem``.

        Parameters
        ----------
        elem : lxml.etree.Element
            XML element to parse

        Returns
        -------
        coefs : ndarray
            2-dimensional array of coefficients ordered so that the coefficient of x=m and y=n is contained in ``val[m, n]``

        """
        shape = (int(elem.get(self.size_x_name)), int(elem.get(self.size_y_name)))
        coefs = np.zeros(shape, np.float64)
        coef_by_indices = {
            (int(coef.get(self.coef_x_name)), int(coef.get(self.coef_y_name))): float(
                coef.text
            )
            for coef in elem
        }
        for indices, coef in coef_by_indices.items():
            coefs[*indices] = coef
        return coefs

    def set_elem(self, elem: lxml.etree.Element, val: npt.ArrayLike) -> None:
        """Set ``elem`` node using the filter coefficients from ``val``.

        Parameters
        ----------
        elem : lxml.etree.Element
            XML element to set
        val : array_like
            2-dimensional array of coefficients ordered so that the coefficient of x=m and y=n is contained in ``val[m, n]``

        """
        coefs = np.asarray(val)
        if coefs.ndim != 2:
            raise ValueError("Filter coefficient array must be 2-dimensional")
        elem[:] = []
        elem_ns = self.child_ns if self.child_ns else lxml.etree.QName(elem).namespace
        ns = f"{{{elem_ns}}}" if elem_ns else ""
        elem.set(self.size_x_name, str(coefs.shape[0]))
        elem.set(self.size_y_name, str(coefs.shape[1]))
        for coord, coef in np.ndenumerate(coefs):
            attribs = {
                self.coef_x_name: str(coord[0]),
                self.coef_y_name: str(coord[1]),
            }
            lxml.etree.SubElement(elem, ns + "Coef", attrib=attribs).text = str(coef)


class IntListType(ssxml.Type):
    """
    Transcoder for ints in a list XML parameter types.

    """

    def parse_elem(self, elem: lxml.etree.Element) -> npt.NDArray:
        """Returns space-separated ints as ndarray of ints"""
        val = "" if elem.text is None else elem.text
        return np.array([int(tok) for tok in val.split(" ")], dtype=int)

    def set_elem(
        self, elem: lxml.etree.Element, val: Sequence[numbers.Integral]
    ) -> None:
        """Sets ``elem`` node using the list of integers in ``val``."""
        elem.text = " ".join([str(entry) for entry in val])


class ImageCornersType(ssxml.ListType):
    """
    Transcoder for GeoData/ImageCorners XML parameter types.

    icp_ns : str, optional
        Namespace to use for ICP elements.  Parent namespace used if unspecified.
    child_ns : str, optional
        Namespace to use for LatLon elements.  ICP namespace used if unspecified.

    """

    def __init__(self, icp_ns: str = "", child_ns: str = "") -> None:
        super().__init__("ICP", ssxml.LatLonType(child_ns=child_ns))
        self.icp_ns = icp_ns

    def parse_elem(self, elem: lxml.etree.Element) -> npt.NDArray:
        """Returns the array of ImageCorners encoded in ``elem``.

        Parameters
        ----------
        elem : lxml.etree.Element
            XML element to parse

        Returns
        -------
        coefs : (4, 2) ndarray
            Array of [latitude (deg), longitude (deg)] image corners.

        """
        return np.asarray(
            [
                self.sub_type.parse_elem(x)
                for x in sorted(elem, key=lambda x: x.get("index"))
            ]
        )

    def set_elem(
        self, elem: lxml.etree.Element, val: Sequence[Sequence[float]]
    ) -> None:
        """Set the ICP children of ``elem`` using the ordered vertices from ``val``.

        Parameters
        ----------
        elem : lxml.etree.Element
            XML element to set
        val : (4, 2) array_like
            Array of [latitude (deg), longitude (deg)] image corners.

        """
        elem[:] = []
        labels = ("1:FRFC", "2:FRLC", "3:LRLC", "4:LRFC")
        icp_ns = self.icp_ns if self.icp_ns else lxml.etree.QName(elem).namespace
        icp_ns = f"{{{icp_ns}}}" if icp_ns else ""
        for label, coord in zip(labels, val):
            icp = lxml.etree.SubElement(
                elem, icp_ns + self.sub_tag, attrib={"index": label}
            )
            self.sub_type.set_elem(icp, coord)


class RangeAzimuthType(ssxml.ArrayType):
    """
    Transcoder for double-precision floating point range and azimuth XML parameter types.

    child_ns : str, optional
        Namespace to use for child elements.  Parent namespace used if unspecified.

    """

    def __init__(self, child_ns: str = "") -> None:
        super().__init__(
            subelements={c: ssxml.DblType() for c in ("Range", "Azimuth")},
            child_ns=child_ns,
        )


class RowColDblType(ssxml.ArrayType):
    """
    Transcoder for double-precision floating point row and column XML parameter types.

    child_ns : str, optional
        Namespace to use for child elements.  Parent namespace used if unspecified.

    """

    def __init__(self, child_ns: str = "") -> None:
        super().__init__(
            subelements={c: ssxml.DblType() for c in ("Row", "Col")}, child_ns=child_ns
        )


class SfaPointType(ssxml.ArrayType):
    """
    Transcoder for double-precision floating point Simple Feature Access 2D or 3D Points.

    """

    def __init__(self) -> None:
        self._subelem_superset: dict[str, ssxml.Type] = {
            c: ssxml.DblType() for c in ("X", "Y", "Z")
        }
        super().__init__(subelements=self._subelem_superset, child_ns="urn:SFA:1.2.0")

    def parse_elem(self, elem: lxml.etree.Element) -> npt.NDArray:
        """Returns an array containing the sub-elements encoded in ``elem``."""
        if len(elem) not in (2, 3):
            raise ValueError("Unexpected number of subelements (requires 2 or 3)")
        self.subelements = {
            k: v
            for idx, (k, v) in enumerate(self._subelem_superset.items())
            if idx < len(elem)
        }
        return super().parse_elem(elem)

    def set_elem(self, elem: lxml.etree.Element, val: Sequence[Any]) -> None:
        """Set ``elem`` node using ``val``."""
        if len(val) not in (2, 3):
            raise ValueError("Unexpected number of values (requires 2 or 3)")
        self.subelements = {
            k: v
            for idx, (k, v) in enumerate(self._subelem_superset.items())
            if idx < len(val)
        }
        super().set_elem(elem, val)


def _expand_lookuptable_nodes(prefix: str):
    return {
        f"{prefix}/LUTName": ssxml.TxtType(),
        f"{prefix}/Predefined/DatabaseName": ssxml.TxtType(),
        f"{prefix}/Predefined/RemapFamily": ssxml.IntType(),
        f"{prefix}/Predefined/RemapMember": ssxml.IntType(),
        f"{prefix}/Custom/LUTInfo/LUTValues": IntListType(),
    }


def _expand_filter_nodes(prefix: str):
    return {
        f"{prefix}/FilterName": ssxml.TxtType(),
        f"{prefix}/FilterKernel/Predefined/DatabaseName": ssxml.TxtType(),
        f"{prefix}/FilterKernel/Predefined/FilterFamily": ssxml.IntType(),
        f"{prefix}/FilterKernel/Predefined/FilterMember": ssxml.IntType(),
        f"{prefix}/FilterKernel/Custom/FilterCoefficients": FilterCoefficientType(
            "rowcol"
        ),
        f"{prefix}/FilterBank/Predefined/DatabaseName": ssxml.TxtType(),
        f"{prefix}/FilterBank/Predefined/FilterFamily": ssxml.IntType(),
        f"{prefix}/FilterBank/Predefined/FilterMember": ssxml.IntType(),
        f"{prefix}/FilterBank/Custom/FilterCoefficients": FilterCoefficientType(
            "phasingpoint"
        ),
        f"{prefix}/Operation": ssxml.TxtType(),
    }


TRANSCODERS: dict[str, ssxml.Type] = {
    "ProductCreation/ProcessorInformation/Application": ssxml.TxtType(),
    "ProductCreation/ProcessorInformation/ProcessingDateTime": ssxml.XdtType(),
    "ProductCreation/ProcessorInformation/Site": ssxml.TxtType(),
    "ProductCreation/ProcessorInformation/Profile": ssxml.TxtType(),
    "ProductCreation/Classification/SecurityExtension": ssxml.ParameterType(),
    "ProductCreation/ProductName": ssxml.TxtType(),
    "ProductCreation/ProductClass": ssxml.TxtType(),
    "ProductCreation/ProductType": ssxml.TxtType(),
    "ProductCreation/ProductCreationExtension": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "Display/PixelType": ssxml.TxtType(),
    "Display/NumBands": ssxml.IntType(),
    "Display/DefaultBandDisplay": ssxml.IntType(),
    "Display/NonInteractiveProcessing/ProductGenerationOptions/BandEqualization/Algorithm": ssxml.TxtType(),
}
TRANSCODERS |= _expand_lookuptable_nodes(
    "Display/NonInteractiveProcessing/ProductGenerationOptions/BandEqualization/BandLUT"
)
TRANSCODERS |= _expand_filter_nodes(
    "Display/NonInteractiveProcessing/ProductGenerationOptions/ModularTransferFunctionRestoration"
)
TRANSCODERS |= _expand_lookuptable_nodes(
    "Display/NonInteractiveProcessing/ProductGenerationOptions/DataRemapping"
)
TRANSCODERS |= _expand_filter_nodes(
    "Display/NonInteractiveProcessing/ProductGenerationOptions/AsymmetricPixelCorrection"
)
TRANSCODERS |= {
    "Display/NonInteractiveProcessing/RRDS/DownsamplingMethod": ssxml.TxtType(),
}
TRANSCODERS |= _expand_filter_nodes("Display/NonInteractiveProcessing/RRDS/AntiAlias")
TRANSCODERS |= _expand_filter_nodes(
    "Display/NonInteractiveProcessing/RRDS/Interpolation"
)
TRANSCODERS |= _expand_filter_nodes(
    "Display/InteractiveProcessing/GeometricTransform/Scaling/AntiAlias"
)
TRANSCODERS |= _expand_filter_nodes(
    "Display/InteractiveProcessing/GeometricTransform/Scaling/Interpolation"
)
TRANSCODERS |= {
    "Display/InteractiveProcessing/GeometricTransform/Orientation/ShadowDirection": ssxml.TxtType(),
}
TRANSCODERS |= _expand_filter_nodes(
    "Display/InteractiveProcessing/SharpnessEnhancement/ModularTransferFunctionCompensation"
)
TRANSCODERS |= _expand_filter_nodes(
    "Display/InteractiveProcessing/SharpnessEnhancement/ModularTransferFunctionEnhancement"
)
TRANSCODERS |= {
    "Display/InteractiveProcessing/ColorSpaceTransform/ColorManagementModule/RenderingIntent": ssxml.TxtType(),
    "Display/InteractiveProcessing/ColorSpaceTransform/ColorManagementModule/SourceProfile": ssxml.TxtType(),
    "Display/InteractiveProcessing/ColorSpaceTransform/ColorManagementModule/DisplayProfile": ssxml.TxtType(),
    "Display/InteractiveProcessing/ColorSpaceTransform/ColorManagementModule/ICCProfileSignature": ssxml.TxtType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/AlgorithmType": ssxml.TxtType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/BandStatsSource": ssxml.IntType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAParameters/Pmin": ssxml.DblType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAParameters/Pmax": ssxml.DblType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAParameters/EminModifier": ssxml.DblType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAParameters/EmaxModifier": ssxml.DblType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAOverrides/Subtractor": ssxml.DblType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAOverrides/Multiplier": ssxml.DblType(),
}
TRANSCODERS |= _expand_lookuptable_nodes(
    "Display/InteractiveProcessing/TonalTransferCurve"
)
TRANSCODERS |= {
    "Display/DisplayExtension": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "GeoData/EarthModel": ssxml.TxtType(),
    "GeoData/ImageCorners": ImageCornersType(child_ns="urn:SICommon:1.0"),
    "GeoData/ValidData": ssxml.ListType(
        "Vertex", ssxml.LatLonType(child_ns="urn:SICommon:1.0")
    ),
    "GeoData/GeoInfo/Desc": ssxml.ParameterType(),
    "GeoData/GeoInfo/Point": ssxml.LatLonType(),
    "GeoData/GeoInfo/Line": ssxml.ListType("Endpoint", ssxml.LatLonType()),
    "GeoData/GeoInfo/Polygon": ssxml.ListType("Vertex", ssxml.LatLonType()),
}
TRANSCODERS |= {
    "Measurement/PlaneProjection/ReferencePoint/ECEF": ssxml.XyzType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PlaneProjection/ReferencePoint/Point": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PlaneProjection/SampleSpacing": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PlaneProjection/TimeCOAPoly": ssxml.PolyType(
        2, child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PlaneProjection/ProductPlane/RowUnitVector": ssxml.XyzType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PlaneProjection/ProductPlane/ColUnitVector": ssxml.XyzType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PolynomialProjection/ReferencePoint/ECEF": ssxml.XyzType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PolynomialProjection/ReferencePoint/Point": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PolynomialProjection/RowColToLat": ssxml.PolyType(
        2, child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PolynomialProjection/RowColToLon": ssxml.PolyType(
        2, child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PolynomialProjection/RowColToAlt": ssxml.PolyType(
        2, child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PolynomialProjection/LatLonToRow": ssxml.PolyType(
        2, child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PolynomialProjection/LatLonToCol": ssxml.PolyType(
        2, child_ns="urn:SICommon:1.0"
    ),
    "Measurement/GeographicProjection/ReferencePoint/ECEF": ssxml.XyzType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/GeographicProjection/ReferencePoint/Point": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/GeographicProjection/SampleSpacing": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/GeographicProjection/TimeCOAPoly": ssxml.PolyType(
        2, child_ns="urn:SICommon:1.0"
    ),
    "Measurement/CylindricalProjection/ReferencePoint/ECEF": ssxml.XyzType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/CylindricalProjection/ReferencePoint/Point": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/CylindricalProjection/SampleSpacing": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/CylindricalProjection/TimeCOAPoly": ssxml.PolyType(
        2, child_ns="urn:SICommon:1.0"
    ),
    "Measurement/CylindricalProjection/StripmapDirection": ssxml.XyzType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/CylindricalProjection/CurvatureRadius": ssxml.DblType(),
    "Measurement/PixelFootprint": ssxml.RowColType(child_ns="urn:SICommon:1.0"),
    "Measurement/ARPFlag": ssxml.TxtType(),
    "Measurement/ARPPoly": ssxml.XyzPolyType(child_ns="urn:SICommon:1.0"),
    "Measurement/ValidData": ssxml.ListType(
        "Vertex", ssxml.RowColType(child_ns="urn:SICommon:1.0")
    ),
}
TRANSCODERS |= {
    "ExploitationFeatures/Collection/Information/SensorName": ssxml.TxtType(),
    "ExploitationFeatures/Collection/Information/RadarMode/ModeType": ssxml.TxtType(),
    "ExploitationFeatures/Collection/Information/RadarMode/ModeID": ssxml.TxtType(),
    "ExploitationFeatures/Collection/Information/CollectionDateTime": ssxml.XdtType(),
    "ExploitationFeatures/Collection/Information/LocalDateTime": ssxml.XdtType(),
    "ExploitationFeatures/Collection/Information/CollectionDuration": ssxml.DblType(),
    "ExploitationFeatures/Collection/Information/Resolution": RangeAzimuthType(
        child_ns="urn:SICommon:1.0"
    ),
    "ExploitationFeatures/Collection/Information/InputROI/Size": ssxml.RowColType(
        child_ns="urn:SICommon:1.0"
    ),
    "ExploitationFeatures/Collection/Information/InputROI/UpperLeft": ssxml.RowColType(
        child_ns="urn:SICommon:1.0"
    ),
    "ExploitationFeatures/Collection/Information/Polarization/TxPolarization": ssxml.TxtType(),
    "ExploitationFeatures/Collection/Information/Polarization/RcvPolarization": ssxml.TxtType(),
    "ExploitationFeatures/Collection/Information/Polarization/RcvPolarizationOffset": ssxml.DblType(),
    "ExploitationFeatures/Collection/Geometry/Azimuth": ssxml.DblType(),
    "ExploitationFeatures/Collection/Geometry/Slope": ssxml.DblType(),
    "ExploitationFeatures/Collection/Geometry/Squint": ssxml.DblType(),
    "ExploitationFeatures/Collection/Geometry/Graze": ssxml.DblType(),
    "ExploitationFeatures/Collection/Geometry/Tilt": ssxml.DblType(),
    "ExploitationFeatures/Collection/Geometry/DopplerConeAngle": ssxml.DblType(),
    "ExploitationFeatures/Collection/Geometry/Extension": ssxml.ParameterType(),
    "ExploitationFeatures/Collection/Phenomenology/Shadow": AngleMagnitudeType(
        child_ns="urn:SICommon:1.0"
    ),
    "ExploitationFeatures/Collection/Phenomenology/Layover": AngleMagnitudeType(
        child_ns="urn:SICommon:1.0"
    ),
    "ExploitationFeatures/Collection/Phenomenology/MultiPath": ssxml.DblType(),
    "ExploitationFeatures/Collection/Phenomenology/GroundTrack": ssxml.DblType(),
    "ExploitationFeatures/Collection/Phenomenology/Extension": ssxml.ParameterType(),
    "ExploitationFeatures/Product/Resolution": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "ExploitationFeatures/Product/Ellipticity": ssxml.DblType(),
    "ExploitationFeatures/Product/Polarization/TxPolarizationProc": ssxml.TxtType(),
    "ExploitationFeatures/Product/Polarization/RcvPolarizationProc": ssxml.TxtType(),
    "ExploitationFeatures/Product/North": ssxml.DblType(),
    "ExploitationFeatures/Product/Extension": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "DownstreamReprocessing/GeometricChip/ChipSize": ssxml.RowColType(
        child_ns="urn:SICommon:1.0"
    ),
    "DownstreamReprocessing/GeometricChip/OriginalUpperLeftCoordinate": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "DownstreamReprocessing/GeometricChip/OriginalUpperRightCoordinate": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "DownstreamReprocessing/GeometricChip/OriginalLowerLeftCoordinate": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "DownstreamReprocessing/GeometricChip/OriginalLowerRightCoordinate": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "DownstreamReprocessing/ProcessingEvent/ApplicationName": ssxml.TxtType(),
    "DownstreamReprocessing/ProcessingEvent/AppliedDateTime": ssxml.XdtType(),
    "DownstreamReprocessing/ProcessingEvent/InterpolationMethod": ssxml.TxtType(),
    "DownstreamReprocessing/ProcessingEvent/Descriptor": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "ErrorStatistics/CompositeSCP/Rg": ssxml.DblType(),
    "ErrorStatistics/CompositeSCP/Az": ssxml.DblType(),
    "ErrorStatistics/CompositeSCP/RgAz": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/Frame": ssxml.TxtType(),
    "ErrorStatistics/Components/PosVelErr/P1": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/P2": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/P3": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/V1": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/V2": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/V3": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P1P2": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P1P3": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P1V1": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P1V2": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P1V3": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P2P3": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P2V1": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P2V2": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P2V3": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P3V1": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P3V2": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P3V3": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/V1V2": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/V1V3": ssxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/V2V3": ssxml.DblType(),
    **sicdxml._decorr_type("ErrorStatistics/Components/PosVelErr/PositionDecorr"),
    "ErrorStatistics/Components/RadarSensor/RangeBias": ssxml.DblType(),
    "ErrorStatistics/Components/RadarSensor/ClockFreqSF": ssxml.DblType(),
    "ErrorStatistics/Components/RadarSensor/TransmitFreqSF": ssxml.DblType(),
    **sicdxml._decorr_type("ErrorStatistics/Components/RadarSensor/RangeBiasDecorr"),
    "ErrorStatistics/Components/TropoError/TropoRangeVertical": ssxml.DblType(),
    "ErrorStatistics/Components/TropoError/TropoRangeSlant": ssxml.DblType(),
    **sicdxml._decorr_type("ErrorStatistics/Components/TropoError/TropoRangeDecorr"),
    "ErrorStatistics/Components/IonoError/IonoRangeVertical": ssxml.DblType(),
    "ErrorStatistics/Components/IonoError/IonoRangeRateVertical": ssxml.DblType(),
    "ErrorStatistics/Components/IonoError/IonoRgRgRateCC": ssxml.DblType(),
    **sicdxml._decorr_type("ErrorStatistics/Components/IonoError/IonoRangeVertDecorr"),
    "ErrorStatistics/Unmodeled/Xrow": ssxml.DblType(),
    "ErrorStatistics/Unmodeled/Ycol": ssxml.DblType(),
    "ErrorStatistics/Unmodeled/XrowYcol": ssxml.DblType(),
    **sicdxml._decorr_type("ErrorStatistics/Unmodeled/UnmodeledDecorr/Xrow"),
    **sicdxml._decorr_type("ErrorStatistics/Unmodeled/UnmodeledDecorr/Ycol"),
    "ErrorStatistics/AdditionalParms/Parameter": ssxml.TxtType(),
}
TRANSCODERS |= {
    "Radiometric/NoiseLevel/NoiseLevelType": ssxml.TxtType(),
    "Radiometric/NoiseLevel/NoisePoly": ssxml.PolyType(2),
    "Radiometric/RCSSFPoly": ssxml.PolyType(2),
    "Radiometric/SigmaZeroSFPoly": ssxml.PolyType(2),
    "Radiometric/BetaZeroSFPoly": ssxml.PolyType(2),
    "Radiometric/SigmaZeroSFIncidenceMap": ssxml.TxtType(),
    "Radiometric/GammaZeroSFPoly": ssxml.PolyType(2),
}
TRANSCODERS |= {
    "MatchInfo/NumMatchTypes": ssxml.IntType(),
    "MatchInfo/MatchType/TypeID": ssxml.TxtType(),
    "MatchInfo/MatchType/CurrentIndex": ssxml.IntType(),
    "MatchInfo/MatchType/NumMatchCollections": ssxml.IntType(),
    "MatchInfo/MatchType/MatchCollection/CoreName": ssxml.TxtType(),
    "MatchInfo/MatchType/MatchCollection/MatchIndex": ssxml.IntType(),
    "MatchInfo/MatchType/MatchCollection/Parameter": ssxml.TxtType(),
}
TRANSCODERS |= {
    "Compression/J2K/Original/NumWaveletLevels": ssxml.IntType(),
    "Compression/J2K/Original/NumBands": ssxml.IntType(),
    "Compression/J2K/Original/LayerInfo/Layer/Bitrate": ssxml.DblType(),
    "Compression/J2K/Parsed/NumWaveletLevels": ssxml.IntType(),
    "Compression/J2K/Parsed/NumBands": ssxml.IntType(),
    "Compression/J2K/Parsed/LayerInfo/Layer/Bitrate": ssxml.DblType(),
}
TRANSCODERS |= {
    "DigitalElevationData/GeographicCoordinates/LongitudeDensity": ssxml.DblType(),
    "DigitalElevationData/GeographicCoordinates/LatitudeDensity": ssxml.DblType(),
    "DigitalElevationData/GeographicCoordinates/ReferenceOrigin": ssxml.LatLonType(
        child_ns="urn:SICommon:1.0"
    ),
    "DigitalElevationData/Geopositioning/CoordinateSystemType": ssxml.TxtType(),
    "DigitalElevationData/Geopositioning/GeodeticDatum": ssxml.TxtType(),
    "DigitalElevationData/Geopositioning/ReferenceEllipsoid": ssxml.TxtType(),
    "DigitalElevationData/Geopositioning/VerticalDatum": ssxml.TxtType(),
    "DigitalElevationData/Geopositioning/SoundingDatum": ssxml.TxtType(),
    "DigitalElevationData/Geopositioning/FalseOrigin": ssxml.IntType(),
    "DigitalElevationData/Geopositioning/UTMGridZoneNumber": ssxml.IntType(),
    "DigitalElevationData/PositionalAccuracy/NumRegions": ssxml.IntType(),
    "DigitalElevationData/PositionalAccuracy/AbsoluteAccuracy/Horizontal": ssxml.DblType(),
    "DigitalElevationData/PositionalAccuracy/AbsoluteAccuracy/Vertical": ssxml.DblType(),
    "DigitalElevationData/PositionalAccuracy/PointToPointAccuracy/Horizontal": ssxml.DblType(),
    "DigitalElevationData/PositionalAccuracy/PointToPointAccuracy/Vertical": ssxml.DblType(),
    "DigitalElevationData/NullValue": ssxml.IntType(),
}
TRANSCODERS |= {
    "ProductProcessing/ProcessingModule/ModuleName": ssxml.ParameterType(),
    "ProductProcessing/ProcessingModule/ModuleParameter": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "Annotations/Annotation/Identifier": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/Csname": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/Csname": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/Datum/Spheroid/SpheriodName": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/Datum/Spheroid/SemiMajorAxis": ssxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/Datum/Spheroid/InverseFlattening": ssxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/PrimeMeridian/Name": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/PrimeMeridian/Longitude": ssxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/AngularUnit": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/LinearUnit": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/Projection/ProjectionName": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/Parameter/ParameterName": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/Parameter/Value": ssxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/LinearUnit": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/Csname": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/Datum/Spheroid/SpheriodName": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/Datum/Spheroid/SemiMajorAxis": ssxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/Datum/Spheroid/InverseFlattening": ssxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/PrimeMeridian/Name": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/PrimeMeridian/Longitude": ssxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/AngularUnit": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/LinearUnit": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/Csname": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/Datum/Spheroid/SpheriodName": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/Datum/Spheroid/SemiMajorAxis": ssxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/Datum/Spheroid/InverseFlattening": ssxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/PrimeMeridian/Name": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/PrimeMeridian/Longitude": ssxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/LinearUnit": ssxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/AxisName": ssxml.TxtType(),
    "Annotations/Annotation/Object/Point": SfaPointType(),
    "Annotations/Annotation/Object/Line/Vertex": SfaPointType(),
    "Annotations/Annotation/Object/LinearRing/Vertex": SfaPointType(),
    "Annotations/Annotation/Object/Polygon/Ring/Vertex": SfaPointType(),
    "Annotations/Annotation/Object/PolyhedralSurface/Patch/Ring/Vertex": SfaPointType(),
    "Annotations/Annotation/Object/MultiPolygon/Element/Ring/Vertex": SfaPointType(),
    "Annotations/Annotation/Object/MultiLineString/Element/Vertex": SfaPointType(),
    "Annotations/Annotation/Object/MultiPoint/Vertex": SfaPointType(),
}

# Polynomial subelements
TRANSCODERS.update(
    {
        f"{p}/{coord}": ssxml.PolyType(1)
        for p, v in TRANSCODERS.items()
        if isinstance(v, ssxml.XyzPolyType)
        for coord in "XYZ"
    }
)
TRANSCODERS.update(
    {
        f"{p}/Coef": ssxml.DblType()
        for p, v in TRANSCODERS.items()
        if isinstance(v, ssxml.PolyType)
    }
)

# Filter subelements
TRANSCODERS.update(
    {
        f"{p}/Coef": ssxml.DblType()
        for p, v in TRANSCODERS.items()
        if isinstance(v, FilterCoefficientType)
    }
)

# List subelements
TRANSCODERS.update(
    {
        f"{p}/{v.sub_tag}": v.sub_type
        for p, v in TRANSCODERS.items()
        if isinstance(v, ssxml.ListType)
    }
)

# Sequence subelements
TRANSCODERS.update(
    {
        f"{p}/{sub_name}": sub_type
        for p, v in TRANSCODERS.items()
        if isinstance(v, ssxml.SequenceType)
        for sub_name, sub_type in v.subelements.items()
    }
)


class XmlHelper(ssxml.XmlHelper):
    """
    XmlHelper for Sensor Independent Derived Data (SIDD).

    """

    _transcoders_ = TRANSCODERS

    def _get_simple_path(self, elem):
        simple_path = re.sub(r"(GeoInfo/)+", "GeoInfo/", super()._get_simple_path(elem))
        simple_path = re.sub(r"(ProcessingModule/)+", "ProcessingModule/", simple_path)
        return simple_path
