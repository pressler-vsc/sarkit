"""
Functions for interacting with SIDD XML
"""

import numbers
import re
from collections.abc import Sequence
from typing import Any

import lxml.etree
import numpy as np
import numpy.typing as npt

import sarkit._xmlhelp as skxml
import sarkit.standards.sicd.xml as sicdxml


class AngleMagnitudeType(skxml.ArrayType):
    """
    Transcoder for double-precision floating point angle magnitude XML parameter type.

    """

    def __init__(self, child_ns: str = "") -> None:
        super().__init__(
            subelements={c: skxml.DblType() for c in ("Angle", "Magnitude")},
            child_ns=child_ns,
        )


class FilterCoefficientType(skxml.Type):
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


class IntListType(skxml.Type):
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


class ImageCornersType(skxml.ListType):
    """
    Transcoder for GeoData/ImageCorners XML parameter types.

    icp_ns : str, optional
        Namespace to use for ICP elements.  Parent namespace used if unspecified.
    child_ns : str, optional
        Namespace to use for LatLon elements.  ICP namespace used if unspecified.

    """

    def __init__(self, icp_ns: str = "", child_ns: str = "") -> None:
        super().__init__("ICP", skxml.LatLonType(child_ns=child_ns))
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


class RangeAzimuthType(skxml.ArrayType):
    """
    Transcoder for double-precision floating point range and azimuth XML parameter types.

    child_ns : str, optional
        Namespace to use for child elements.  Parent namespace used if unspecified.

    """

    def __init__(self, child_ns: str = "") -> None:
        super().__init__(
            subelements={c: skxml.DblType() for c in ("Range", "Azimuth")},
            child_ns=child_ns,
        )


class RowColDblType(skxml.ArrayType):
    """
    Transcoder for double-precision floating point row and column XML parameter types.

    child_ns : str, optional
        Namespace to use for child elements.  Parent namespace used if unspecified.

    """

    def __init__(self, child_ns: str = "") -> None:
        super().__init__(
            subelements={c: skxml.DblType() for c in ("Row", "Col")}, child_ns=child_ns
        )


class SfaPointType(skxml.ArrayType):
    """
    Transcoder for double-precision floating point Simple Feature Access 2D or 3D Points.

    """

    def __init__(self) -> None:
        self._subelem_superset: dict[str, skxml.Type] = {
            c: skxml.DblType() for c in ("X", "Y", "Z")
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
        f"{prefix}/LUTName": skxml.TxtType(),
        f"{prefix}/Predefined/DatabaseName": skxml.TxtType(),
        f"{prefix}/Predefined/RemapFamily": skxml.IntType(),
        f"{prefix}/Predefined/RemapMember": skxml.IntType(),
        f"{prefix}/Custom/LUTInfo/LUTValues": IntListType(),
    }


def _expand_filter_nodes(prefix: str):
    return {
        f"{prefix}/FilterName": skxml.TxtType(),
        f"{prefix}/FilterKernel/Predefined/DatabaseName": skxml.TxtType(),
        f"{prefix}/FilterKernel/Predefined/FilterFamily": skxml.IntType(),
        f"{prefix}/FilterKernel/Predefined/FilterMember": skxml.IntType(),
        f"{prefix}/FilterKernel/Custom/FilterCoefficients": FilterCoefficientType(
            "rowcol"
        ),
        f"{prefix}/FilterBank/Predefined/DatabaseName": skxml.TxtType(),
        f"{prefix}/FilterBank/Predefined/FilterFamily": skxml.IntType(),
        f"{prefix}/FilterBank/Predefined/FilterMember": skxml.IntType(),
        f"{prefix}/FilterBank/Custom/FilterCoefficients": FilterCoefficientType(
            "phasingpoint"
        ),
        f"{prefix}/Operation": skxml.TxtType(),
    }


TRANSCODERS: dict[str, skxml.Type] = {
    "ProductCreation/ProcessorInformation/Application": skxml.TxtType(),
    "ProductCreation/ProcessorInformation/ProcessingDateTime": skxml.XdtType(),
    "ProductCreation/ProcessorInformation/Site": skxml.TxtType(),
    "ProductCreation/ProcessorInformation/Profile": skxml.TxtType(),
    "ProductCreation/Classification/SecurityExtension": skxml.ParameterType(),
    "ProductCreation/ProductName": skxml.TxtType(),
    "ProductCreation/ProductClass": skxml.TxtType(),
    "ProductCreation/ProductType": skxml.TxtType(),
    "ProductCreation/ProductCreationExtension": skxml.ParameterType(),
}
TRANSCODERS |= {
    "Display/PixelType": skxml.TxtType(),
    "Display/NumBands": skxml.IntType(),
    "Display/DefaultBandDisplay": skxml.IntType(),
    "Display/NonInteractiveProcessing/ProductGenerationOptions/BandEqualization/Algorithm": skxml.TxtType(),
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
    "Display/NonInteractiveProcessing/RRDS/DownsamplingMethod": skxml.TxtType(),
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
    "Display/InteractiveProcessing/GeometricTransform/Orientation/ShadowDirection": skxml.TxtType(),
}
TRANSCODERS |= _expand_filter_nodes(
    "Display/InteractiveProcessing/SharpnessEnhancement/ModularTransferFunctionCompensation"
)
TRANSCODERS |= _expand_filter_nodes(
    "Display/InteractiveProcessing/SharpnessEnhancement/ModularTransferFunctionEnhancement"
)
TRANSCODERS |= {
    "Display/InteractiveProcessing/ColorSpaceTransform/ColorManagementModule/RenderingIntent": skxml.TxtType(),
    "Display/InteractiveProcessing/ColorSpaceTransform/ColorManagementModule/SourceProfile": skxml.TxtType(),
    "Display/InteractiveProcessing/ColorSpaceTransform/ColorManagementModule/DisplayProfile": skxml.TxtType(),
    "Display/InteractiveProcessing/ColorSpaceTransform/ColorManagementModule/ICCProfileSignature": skxml.TxtType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/AlgorithmType": skxml.TxtType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/BandStatsSource": skxml.IntType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAParameters/Pmin": skxml.DblType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAParameters/Pmax": skxml.DblType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAParameters/EminModifier": skxml.DblType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAParameters/EmaxModifier": skxml.DblType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAOverrides/Subtractor": skxml.DblType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAOverrides/Multiplier": skxml.DblType(),
}
TRANSCODERS |= _expand_lookuptable_nodes(
    "Display/InteractiveProcessing/TonalTransferCurve"
)
TRANSCODERS |= {
    "Display/DisplayExtension": skxml.ParameterType(),
}
TRANSCODERS |= {
    "GeoData/EarthModel": skxml.TxtType(),
    "GeoData/ImageCorners": ImageCornersType(child_ns="urn:SICommon:1.0"),
    "GeoData/ValidData": skxml.ListType(
        "Vertex", skxml.LatLonType(child_ns="urn:SICommon:1.0")
    ),
    "GeoData/GeoInfo/Desc": skxml.ParameterType(),
    "GeoData/GeoInfo/Point": skxml.LatLonType(),
    "GeoData/GeoInfo/Line": skxml.ListType("Endpoint", skxml.LatLonType()),
    "GeoData/GeoInfo/Polygon": skxml.ListType("Vertex", skxml.LatLonType()),
}
TRANSCODERS |= {
    "Measurement/PlaneProjection/ReferencePoint/ECEF": skxml.XyzType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PlaneProjection/ReferencePoint/Point": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PlaneProjection/SampleSpacing": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PlaneProjection/TimeCOAPoly": skxml.Poly2dType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PlaneProjection/ProductPlane/RowUnitVector": skxml.XyzType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PlaneProjection/ProductPlane/ColUnitVector": skxml.XyzType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PolynomialProjection/ReferencePoint/ECEF": skxml.XyzType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PolynomialProjection/ReferencePoint/Point": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PolynomialProjection/RowColToLat": skxml.Poly2dType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PolynomialProjection/RowColToLon": skxml.Poly2dType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PolynomialProjection/RowColToAlt": skxml.Poly2dType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PolynomialProjection/LatLonToRow": skxml.Poly2dType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/PolynomialProjection/LatLonToCol": skxml.Poly2dType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/GeographicProjection/ReferencePoint/ECEF": skxml.XyzType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/GeographicProjection/ReferencePoint/Point": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/GeographicProjection/SampleSpacing": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/GeographicProjection/TimeCOAPoly": skxml.Poly2dType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/CylindricalProjection/ReferencePoint/ECEF": skxml.XyzType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/CylindricalProjection/ReferencePoint/Point": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/CylindricalProjection/SampleSpacing": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/CylindricalProjection/TimeCOAPoly": skxml.Poly2dType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/CylindricalProjection/StripmapDirection": skxml.XyzType(
        child_ns="urn:SICommon:1.0"
    ),
    "Measurement/CylindricalProjection/CurvatureRadius": skxml.DblType(),
    "Measurement/PixelFootprint": skxml.RowColType(child_ns="urn:SICommon:1.0"),
    "Measurement/ARPFlag": skxml.TxtType(),
    "Measurement/ARPPoly": skxml.XyzPolyType(child_ns="urn:SICommon:1.0"),
    "Measurement/ValidData": skxml.ListType(
        "Vertex", skxml.RowColType(child_ns="urn:SICommon:1.0")
    ),
}
TRANSCODERS |= {
    "ExploitationFeatures/Collection/Information/SensorName": skxml.TxtType(),
    "ExploitationFeatures/Collection/Information/RadarMode/ModeType": skxml.TxtType(),
    "ExploitationFeatures/Collection/Information/RadarMode/ModeID": skxml.TxtType(),
    "ExploitationFeatures/Collection/Information/CollectionDateTime": skxml.XdtType(),
    "ExploitationFeatures/Collection/Information/LocalDateTime": skxml.XdtType(),
    "ExploitationFeatures/Collection/Information/CollectionDuration": skxml.DblType(),
    "ExploitationFeatures/Collection/Information/Resolution": RangeAzimuthType(
        child_ns="urn:SICommon:1.0"
    ),
    "ExploitationFeatures/Collection/Information/InputROI/Size": skxml.RowColType(
        child_ns="urn:SICommon:1.0"
    ),
    "ExploitationFeatures/Collection/Information/InputROI/UpperLeft": skxml.RowColType(
        child_ns="urn:SICommon:1.0"
    ),
    "ExploitationFeatures/Collection/Information/Polarization/TxPolarization": skxml.TxtType(),
    "ExploitationFeatures/Collection/Information/Polarization/RcvPolarization": skxml.TxtType(),
    "ExploitationFeatures/Collection/Information/Polarization/RcvPolarizationOffset": skxml.DblType(),
    "ExploitationFeatures/Collection/Geometry/Azimuth": skxml.DblType(),
    "ExploitationFeatures/Collection/Geometry/Slope": skxml.DblType(),
    "ExploitationFeatures/Collection/Geometry/Squint": skxml.DblType(),
    "ExploitationFeatures/Collection/Geometry/Graze": skxml.DblType(),
    "ExploitationFeatures/Collection/Geometry/Tilt": skxml.DblType(),
    "ExploitationFeatures/Collection/Geometry/DopplerConeAngle": skxml.DblType(),
    "ExploitationFeatures/Collection/Geometry/Extension": skxml.ParameterType(),
    "ExploitationFeatures/Collection/Phenomenology/Shadow": AngleMagnitudeType(
        child_ns="urn:SICommon:1.0"
    ),
    "ExploitationFeatures/Collection/Phenomenology/Layover": AngleMagnitudeType(
        child_ns="urn:SICommon:1.0"
    ),
    "ExploitationFeatures/Collection/Phenomenology/MultiPath": skxml.DblType(),
    "ExploitationFeatures/Collection/Phenomenology/GroundTrack": skxml.DblType(),
    "ExploitationFeatures/Collection/Phenomenology/Extension": skxml.ParameterType(),
    "ExploitationFeatures/Product/Resolution": RowColDblType(
        child_ns="urn:SICommon:1.0"
    ),
    "ExploitationFeatures/Product/Ellipticity": skxml.DblType(),
    "ExploitationFeatures/Product/Polarization/TxPolarizationProc": skxml.TxtType(),
    "ExploitationFeatures/Product/Polarization/RcvPolarizationProc": skxml.TxtType(),
    "ExploitationFeatures/Product/North": skxml.DblType(),
    "ExploitationFeatures/Product/Extension": skxml.ParameterType(),
}
TRANSCODERS |= {
    "DownstreamReprocessing/GeometricChip/ChipSize": skxml.RowColType(
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
    "DownstreamReprocessing/ProcessingEvent/ApplicationName": skxml.TxtType(),
    "DownstreamReprocessing/ProcessingEvent/AppliedDateTime": skxml.XdtType(),
    "DownstreamReprocessing/ProcessingEvent/InterpolationMethod": skxml.TxtType(),
    "DownstreamReprocessing/ProcessingEvent/Descriptor": skxml.ParameterType(),
}
TRANSCODERS |= {
    "ErrorStatistics/CompositeSCP/Rg": skxml.DblType(),
    "ErrorStatistics/CompositeSCP/Az": skxml.DblType(),
    "ErrorStatistics/CompositeSCP/RgAz": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/Frame": skxml.TxtType(),
    "ErrorStatistics/Components/PosVelErr/P1": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/P2": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/P3": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/V1": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/V2": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/V3": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P1P2": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P1P3": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P1V1": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P1V2": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P1V3": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P2P3": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P2V1": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P2V2": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P2V3": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P3V1": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P3V2": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P3V3": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/V1V2": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/V1V3": skxml.DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/V2V3": skxml.DblType(),
    **sicdxml._decorr_type("ErrorStatistics/Components/PosVelErr/PositionDecorr"),
    "ErrorStatistics/Components/RadarSensor/RangeBias": skxml.DblType(),
    "ErrorStatistics/Components/RadarSensor/ClockFreqSF": skxml.DblType(),
    "ErrorStatistics/Components/RadarSensor/TransmitFreqSF": skxml.DblType(),
    **sicdxml._decorr_type("ErrorStatistics/Components/RadarSensor/RangeBiasDecorr"),
    "ErrorStatistics/Components/TropoError/TropoRangeVertical": skxml.DblType(),
    "ErrorStatistics/Components/TropoError/TropoRangeSlant": skxml.DblType(),
    **sicdxml._decorr_type("ErrorStatistics/Components/TropoError/TropoRangeDecorr"),
    "ErrorStatistics/Components/IonoError/IonoRangeVertical": skxml.DblType(),
    "ErrorStatistics/Components/IonoError/IonoRangeRateVertical": skxml.DblType(),
    "ErrorStatistics/Components/IonoError/IonoRgRgRateCC": skxml.DblType(),
    **sicdxml._decorr_type("ErrorStatistics/Components/IonoError/IonoRangeVertDecorr"),
    "ErrorStatistics/Unmodeled/Xrow": skxml.DblType(),
    "ErrorStatistics/Unmodeled/Ycol": skxml.DblType(),
    "ErrorStatistics/Unmodeled/XrowYcol": skxml.DblType(),
    **sicdxml._decorr_type("ErrorStatistics/Unmodeled/UnmodeledDecorr/Xrow"),
    **sicdxml._decorr_type("ErrorStatistics/Unmodeled/UnmodeledDecorr/Ycol"),
    "ErrorStatistics/AdditionalParms/Parameter": skxml.TxtType(),
}
TRANSCODERS |= {
    "Radiometric/NoiseLevel/NoiseLevelType": skxml.TxtType(),
    "Radiometric/NoiseLevel/NoisePoly": skxml.Poly2dType(),
    "Radiometric/RCSSFPoly": skxml.Poly2dType(),
    "Radiometric/SigmaZeroSFPoly": skxml.Poly2dType(),
    "Radiometric/BetaZeroSFPoly": skxml.Poly2dType(),
    "Radiometric/SigmaZeroSFIncidenceMap": skxml.TxtType(),
    "Radiometric/GammaZeroSFPoly": skxml.Poly2dType(),
}
TRANSCODERS |= {
    "MatchInfo/NumMatchTypes": skxml.IntType(),
    "MatchInfo/MatchType/TypeID": skxml.TxtType(),
    "MatchInfo/MatchType/CurrentIndex": skxml.IntType(),
    "MatchInfo/MatchType/NumMatchCollections": skxml.IntType(),
    "MatchInfo/MatchType/MatchCollection/CoreName": skxml.TxtType(),
    "MatchInfo/MatchType/MatchCollection/MatchIndex": skxml.IntType(),
    "MatchInfo/MatchType/MatchCollection/Parameter": skxml.TxtType(),
}
TRANSCODERS |= {
    "Compression/J2K/Original/NumWaveletLevels": skxml.IntType(),
    "Compression/J2K/Original/NumBands": skxml.IntType(),
    "Compression/J2K/Original/LayerInfo/Layer/Bitrate": skxml.DblType(),
    "Compression/J2K/Parsed/NumWaveletLevels": skxml.IntType(),
    "Compression/J2K/Parsed/NumBands": skxml.IntType(),
    "Compression/J2K/Parsed/LayerInfo/Layer/Bitrate": skxml.DblType(),
}
TRANSCODERS |= {
    "DigitalElevationData/GeographicCoordinates/LongitudeDensity": skxml.DblType(),
    "DigitalElevationData/GeographicCoordinates/LatitudeDensity": skxml.DblType(),
    "DigitalElevationData/GeographicCoordinates/ReferenceOrigin": skxml.LatLonType(
        child_ns="urn:SICommon:1.0"
    ),
    "DigitalElevationData/Geopositioning/CoordinateSystemType": skxml.TxtType(),
    "DigitalElevationData/Geopositioning/GeodeticDatum": skxml.TxtType(),
    "DigitalElevationData/Geopositioning/ReferenceEllipsoid": skxml.TxtType(),
    "DigitalElevationData/Geopositioning/VerticalDatum": skxml.TxtType(),
    "DigitalElevationData/Geopositioning/SoundingDatum": skxml.TxtType(),
    "DigitalElevationData/Geopositioning/FalseOrigin": skxml.IntType(),
    "DigitalElevationData/Geopositioning/UTMGridZoneNumber": skxml.IntType(),
    "DigitalElevationData/PositionalAccuracy/NumRegions": skxml.IntType(),
    "DigitalElevationData/PositionalAccuracy/AbsoluteAccuracy/Horizontal": skxml.DblType(),
    "DigitalElevationData/PositionalAccuracy/AbsoluteAccuracy/Vertical": skxml.DblType(),
    "DigitalElevationData/PositionalAccuracy/PointToPointAccuracy/Horizontal": skxml.DblType(),
    "DigitalElevationData/PositionalAccuracy/PointToPointAccuracy/Vertical": skxml.DblType(),
    "DigitalElevationData/NullValue": skxml.IntType(),
}
TRANSCODERS |= {
    "ProductProcessing/ProcessingModule/ModuleName": skxml.ParameterType(),
    "ProductProcessing/ProcessingModule/ModuleParameter": skxml.ParameterType(),
}
TRANSCODERS |= {
    "Annotations/Annotation/Identifier": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/Csname": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/Csname": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/Datum/Spheroid/SpheriodName": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/Datum/Spheroid/SemiMajorAxis": skxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/Datum/Spheroid/InverseFlattening": skxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/PrimeMeridian/Name": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/PrimeMeridian/Longitude": skxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/AngularUnit": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/LinearUnit": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/Projection/ProjectionName": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/Parameter/ParameterName": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/Parameter/Value": skxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/LinearUnit": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/Csname": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/Datum/Spheroid/SpheriodName": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/Datum/Spheroid/SemiMajorAxis": skxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/Datum/Spheroid/InverseFlattening": skxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/PrimeMeridian/Name": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/PrimeMeridian/Longitude": skxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/AngularUnit": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/LinearUnit": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/Csname": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/Datum/Spheroid/SpheriodName": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/Datum/Spheroid/SemiMajorAxis": skxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/Datum/Spheroid/InverseFlattening": skxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/PrimeMeridian/Name": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/PrimeMeridian/Longitude": skxml.DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/LinearUnit": skxml.TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/AxisName": skxml.TxtType(),
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
        f"{p}/{coord}": skxml.PolyType()
        for p, v in TRANSCODERS.items()
        if isinstance(v, skxml.XyzPolyType)
        for coord in "XYZ"
    }
)
TRANSCODERS.update(
    {
        f"{p}/Coef": skxml.DblType()
        for p, v in TRANSCODERS.items()
        if isinstance(v, skxml.PolyNdType)
    }
)

# Filter subelements
TRANSCODERS.update(
    {
        f"{p}/Coef": skxml.DblType()
        for p, v in TRANSCODERS.items()
        if isinstance(v, FilterCoefficientType)
    }
)

# List subelements
TRANSCODERS.update(
    {
        f"{p}/{v.sub_tag}": v.sub_type
        for p, v in TRANSCODERS.items()
        if isinstance(v, skxml.ListType)
    }
)

# Sequence subelements
TRANSCODERS.update(
    {
        f"{p}/{sub_name}": sub_type
        for p, v in TRANSCODERS.items()
        if isinstance(v, skxml.SequenceType)
        for sub_name, sub_type in v.subelements.items()
    }
)


class XmlHelper(skxml.XmlHelper):
    """
    XmlHelper for Sensor Independent Derived Data (SIDD).

    """

    _transcoders_ = TRANSCODERS

    def _get_simple_path(self, elem):
        simple_path = re.sub(r"(GeoInfo/)+", "GeoInfo/", super()._get_simple_path(elem))
        simple_path = re.sub(r"(ProcessingModule/)+", "ProcessingModule/", simple_path)
        return simple_path
