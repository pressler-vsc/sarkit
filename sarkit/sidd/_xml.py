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

NSMAP = {
    "sicommon": "urn:SICommon:1.0",
}


# The following transcoders happen to share common implementation across several standards
@skxml.inheritdocstring
class BoolType(skxml.BoolType):
    pass


@skxml.inheritdocstring
class DblType(skxml.DblType):
    pass


@skxml.inheritdocstring
class EnuType(skxml.EnuType):
    pass


@skxml.inheritdocstring
class IntType(skxml.IntType):
    pass


@skxml.inheritdocstring
class TxtType(skxml.TxtType):
    pass


@skxml.inheritdocstring
class XdtType(skxml.XdtType):
    pass


class XyzType(skxml.XyzType):
    """Transcoder for XML parameter types containing scalar X, Y, and Z components.

    Children are in the SICommon namespace.
    """

    def __init__(self):
        super().__init__(child_ns=NSMAP["sicommon"])


class AngleMagnitudeType(skxml.ArrayType):
    """Transcoder for double-precision floating point angle magnitude XML parameter type.

    Children are in the SICommon namespace.
    """

    def __init__(self) -> None:
        super().__init__(
            subelements={c: skxml.DblType() for c in ("Angle", "Magnitude")},
            child_ns=NSMAP["sicommon"],
        )


class LatLonType(skxml.LatLonType):
    """Transcoder for XML parameter types containing scalar Lat and Lon components.

    Children are in the SICommon namespace.
    """

    def __init__(self):
        super().__init__(child_ns=NSMAP["sicommon"])


@skxml.inheritdocstring
class ParameterType(skxml.ParameterType):
    pass


class PolyCoef1dType(skxml.PolyType):
    """Transcoder for one-dimensional polynomial (PolyCoef1D) XML parameter types.

    Children are in the SICommon namespace.
    """

    def __init__(self):
        super().__init__(child_ns=NSMAP["sicommon"])


class PolyCoef2dType(skxml.Poly2dType):
    """Transcoder for two-dimensional polynomial (PolyCoef2D) XML parameter types.

    Children are in the SICommon namespace.
    """

    def __init__(self):
        super().__init__(child_ns=NSMAP["sicommon"])


class RowColIntType(skxml.RowColType):
    """Transcoder for XML parameter types containing scalar, integer Row and Col components (RC_INT).

    Children are in the SICommon namespace.
    """

    def __init__(self):
        super().__init__(child_ns=NSMAP["sicommon"])


class XyzPolyType(skxml.XyzPolyType):
    """Transcoder for XYZ_POLY XML parameter types containing triplets of 1D polynomials.

    Children are in the SICommon namespace.
    """

    def __init__(self):
        super().__init__(child_ns=NSMAP["sicommon"])


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

    Lat/Lon children are in SICommon namespace.
    """

    def __init__(self) -> None:
        super().__init__("ICP", LatLonType())

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
        icp_ns = lxml.etree.QName(elem).namespace
        icp_ns = f"{{{icp_ns}}}" if icp_ns else ""
        for label, coord in zip(labels, val):
            icp = lxml.etree.SubElement(
                elem, icp_ns + self.sub_tag, attrib={"index": label}
            )
            self.sub_type.set_elem(icp, coord)


class RangeAzimuthType(skxml.ArrayType):
    """
    Transcoder for double-precision floating point range and azimuth XML parameter types.

    Children are in the SICommon namespace.

    """

    def __init__(self) -> None:
        super().__init__(
            subelements={c: skxml.DblType() for c in ("Range", "Azimuth")},
            child_ns=NSMAP["sicommon"],
        )


class RowColDblType(skxml.ArrayType):
    """
    Transcoder for double-precision floating point row and column XML parameter types.

    Children are in the SICommon namespace.

    """

    def __init__(self) -> None:
        super().__init__(
            subelements={c: skxml.DblType() for c in ("Row", "Col")},
            child_ns=NSMAP["sicommon"],
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
        f"{prefix}/LUTName": TxtType(),
        f"{prefix}/Predefined/DatabaseName": TxtType(),
        f"{prefix}/Predefined/RemapFamily": IntType(),
        f"{prefix}/Predefined/RemapMember": IntType(),
        f"{prefix}/Custom/LUTInfo/LUTValues": IntListType(),
    }


def _expand_filter_nodes(prefix: str):
    return {
        f"{prefix}/FilterName": TxtType(),
        f"{prefix}/FilterKernel/Predefined/DatabaseName": TxtType(),
        f"{prefix}/FilterKernel/Predefined/FilterFamily": IntType(),
        f"{prefix}/FilterKernel/Predefined/FilterMember": IntType(),
        f"{prefix}/FilterKernel/Custom/FilterCoefficients": FilterCoefficientType(
            "rowcol"
        ),
        f"{prefix}/FilterBank/Predefined/DatabaseName": TxtType(),
        f"{prefix}/FilterBank/Predefined/FilterFamily": IntType(),
        f"{prefix}/FilterBank/Predefined/FilterMember": IntType(),
        f"{prefix}/FilterBank/Custom/FilterCoefficients": FilterCoefficientType(
            "phasingpoint"
        ),
        f"{prefix}/Operation": TxtType(),
    }


def _decorr_type(xml_path):
    return {f"{xml_path}/{x}": skxml.DblType() for x in ("CorrCoefZero", "DecorrRate")}


TRANSCODERS: dict[str, skxml.Type] = {
    "ProductCreation/ProcessorInformation/Application": TxtType(),
    "ProductCreation/ProcessorInformation/ProcessingDateTime": XdtType(),
    "ProductCreation/ProcessorInformation/Site": TxtType(),
    "ProductCreation/ProcessorInformation/Profile": TxtType(),
    "ProductCreation/Classification/SecurityExtension": ParameterType(),
    "ProductCreation/ProductName": TxtType(),
    "ProductCreation/ProductClass": TxtType(),
    "ProductCreation/ProductType": TxtType(),
    "ProductCreation/ProductCreationExtension": ParameterType(),
}
TRANSCODERS |= {
    "Display/PixelType": TxtType(),
    "Display/NumBands": IntType(),
    "Display/DefaultBandDisplay": IntType(),
    "Display/NonInteractiveProcessing/ProductGenerationOptions/BandEqualization/Algorithm": TxtType(),
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
    "Display/NonInteractiveProcessing/RRDS/DownsamplingMethod": TxtType(),
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
    "Display/InteractiveProcessing/GeometricTransform/Orientation/ShadowDirection": TxtType(),
}
TRANSCODERS |= _expand_filter_nodes(
    "Display/InteractiveProcessing/SharpnessEnhancement/ModularTransferFunctionCompensation"
)
TRANSCODERS |= _expand_filter_nodes(
    "Display/InteractiveProcessing/SharpnessEnhancement/ModularTransferFunctionEnhancement"
)
TRANSCODERS |= {
    "Display/InteractiveProcessing/ColorSpaceTransform/ColorManagementModule/RenderingIntent": TxtType(),
    "Display/InteractiveProcessing/ColorSpaceTransform/ColorManagementModule/SourceProfile": TxtType(),
    "Display/InteractiveProcessing/ColorSpaceTransform/ColorManagementModule/DisplayProfile": TxtType(),
    "Display/InteractiveProcessing/ColorSpaceTransform/ColorManagementModule/ICCProfileSignature": TxtType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/AlgorithmType": TxtType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/BandStatsSource": IntType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAParameters/Pmin": DblType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAParameters/Pmax": DblType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAParameters/EminModifier": DblType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAParameters/EmaxModifier": DblType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAOverrides/Subtractor": DblType(),
    "Display/InteractiveProcessing/DynamicRangeAdjustment/DRAOverrides/Multiplier": DblType(),
}
TRANSCODERS |= _expand_lookuptable_nodes(
    "Display/InteractiveProcessing/TonalTransferCurve"
)
TRANSCODERS |= {
    "Display/DisplayExtension": ParameterType(),
}
TRANSCODERS |= {
    "GeoData/EarthModel": TxtType(),
    "GeoData/ImageCorners": ImageCornersType(),
    "GeoData/ValidData": skxml.ListType("Vertex", LatLonType()),
    "GeoData/GeoInfo/Desc": ParameterType(),
    "GeoData/GeoInfo/Point": LatLonType(),
    "GeoData/GeoInfo/Line": skxml.ListType("Endpoint", LatLonType()),
    "GeoData/GeoInfo/Polygon": skxml.ListType("Vertex", LatLonType()),
}
TRANSCODERS |= {
    "Measurement/PlaneProjection/ReferencePoint/ECEF": XyzType(),
    "Measurement/PlaneProjection/ReferencePoint/Point": RowColDblType(),
    "Measurement/PlaneProjection/SampleSpacing": RowColDblType(),
    "Measurement/PlaneProjection/TimeCOAPoly": PolyCoef2dType(),
    "Measurement/PlaneProjection/ProductPlane/RowUnitVector": XyzType(),
    "Measurement/PlaneProjection/ProductPlane/ColUnitVector": XyzType(),
    "Measurement/PolynomialProjection/ReferencePoint/ECEF": XyzType(),
    "Measurement/PolynomialProjection/ReferencePoint/Point": RowColDblType(),
    "Measurement/PolynomialProjection/RowColToLat": PolyCoef2dType(),
    "Measurement/PolynomialProjection/RowColToLon": PolyCoef2dType(),
    "Measurement/PolynomialProjection/RowColToAlt": PolyCoef2dType(),
    "Measurement/PolynomialProjection/LatLonToRow": PolyCoef2dType(),
    "Measurement/PolynomialProjection/LatLonToCol": PolyCoef2dType(),
    "Measurement/GeographicProjection/ReferencePoint/ECEF": XyzType(),
    "Measurement/GeographicProjection/ReferencePoint/Point": RowColDblType(),
    "Measurement/GeographicProjection/SampleSpacing": RowColDblType(),
    "Measurement/GeographicProjection/TimeCOAPoly": PolyCoef2dType(),
    "Measurement/CylindricalProjection/ReferencePoint/ECEF": XyzType(),
    "Measurement/CylindricalProjection/ReferencePoint/Point": RowColDblType(),
    "Measurement/CylindricalProjection/SampleSpacing": RowColDblType(),
    "Measurement/CylindricalProjection/TimeCOAPoly": PolyCoef2dType(),
    "Measurement/CylindricalProjection/StripmapDirection": XyzType(),
    "Measurement/CylindricalProjection/CurvatureRadius": DblType(),
    "Measurement/PixelFootprint": RowColIntType(),
    "Measurement/ARPFlag": TxtType(),
    "Measurement/ARPPoly": XyzPolyType(),
    "Measurement/ValidData": skxml.ListType("Vertex", RowColIntType()),
}
TRANSCODERS |= {
    "ExploitationFeatures/Collection/Information/SensorName": TxtType(),
    "ExploitationFeatures/Collection/Information/RadarMode/ModeType": TxtType(),
    "ExploitationFeatures/Collection/Information/RadarMode/ModeID": TxtType(),
    "ExploitationFeatures/Collection/Information/CollectionDateTime": XdtType(),
    "ExploitationFeatures/Collection/Information/LocalDateTime": XdtType(),
    "ExploitationFeatures/Collection/Information/CollectionDuration": DblType(),
    "ExploitationFeatures/Collection/Information/Resolution": RangeAzimuthType(),
    "ExploitationFeatures/Collection/Information/InputROI/Size": RowColIntType(),
    "ExploitationFeatures/Collection/Information/InputROI/UpperLeft": RowColIntType(),
    "ExploitationFeatures/Collection/Information/Polarization/TxPolarization": TxtType(),
    "ExploitationFeatures/Collection/Information/Polarization/RcvPolarization": TxtType(),
    "ExploitationFeatures/Collection/Information/Polarization/RcvPolarizationOffset": DblType(),
    "ExploitationFeatures/Collection/Geometry/Azimuth": DblType(),
    "ExploitationFeatures/Collection/Geometry/Slope": DblType(),
    "ExploitationFeatures/Collection/Geometry/Squint": DblType(),
    "ExploitationFeatures/Collection/Geometry/Graze": DblType(),
    "ExploitationFeatures/Collection/Geometry/Tilt": DblType(),
    "ExploitationFeatures/Collection/Geometry/DopplerConeAngle": DblType(),
    "ExploitationFeatures/Collection/Geometry/Extension": ParameterType(),
    "ExploitationFeatures/Collection/Phenomenology/Shadow": AngleMagnitudeType(),
    "ExploitationFeatures/Collection/Phenomenology/Layover": AngleMagnitudeType(),
    "ExploitationFeatures/Collection/Phenomenology/MultiPath": DblType(),
    "ExploitationFeatures/Collection/Phenomenology/GroundTrack": DblType(),
    "ExploitationFeatures/Collection/Phenomenology/Extension": ParameterType(),
    "ExploitationFeatures/Product/Resolution": RowColDblType(),
    "ExploitationFeatures/Product/Ellipticity": DblType(),
    "ExploitationFeatures/Product/Polarization/TxPolarizationProc": TxtType(),
    "ExploitationFeatures/Product/Polarization/RcvPolarizationProc": TxtType(),
    "ExploitationFeatures/Product/North": DblType(),
    "ExploitationFeatures/Product/Extension": ParameterType(),
}
TRANSCODERS |= {
    "DownstreamReprocessing/GeometricChip/ChipSize": RowColIntType(),
    "DownstreamReprocessing/GeometricChip/OriginalUpperLeftCoordinate": RowColDblType(),
    "DownstreamReprocessing/GeometricChip/OriginalUpperRightCoordinate": RowColDblType(),
    "DownstreamReprocessing/GeometricChip/OriginalLowerLeftCoordinate": RowColDblType(),
    "DownstreamReprocessing/GeometricChip/OriginalLowerRightCoordinate": RowColDblType(),
    "DownstreamReprocessing/ProcessingEvent/ApplicationName": TxtType(),
    "DownstreamReprocessing/ProcessingEvent/AppliedDateTime": XdtType(),
    "DownstreamReprocessing/ProcessingEvent/InterpolationMethod": TxtType(),
    "DownstreamReprocessing/ProcessingEvent/Descriptor": ParameterType(),
}
TRANSCODERS |= {
    "ErrorStatistics/CompositeSCP/Rg": DblType(),
    "ErrorStatistics/CompositeSCP/Az": DblType(),
    "ErrorStatistics/CompositeSCP/RgAz": DblType(),
    "ErrorStatistics/Components/PosVelErr/Frame": TxtType(),
    "ErrorStatistics/Components/PosVelErr/P1": DblType(),
    "ErrorStatistics/Components/PosVelErr/P2": DblType(),
    "ErrorStatistics/Components/PosVelErr/P3": DblType(),
    "ErrorStatistics/Components/PosVelErr/V1": DblType(),
    "ErrorStatistics/Components/PosVelErr/V2": DblType(),
    "ErrorStatistics/Components/PosVelErr/V3": DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P1P2": DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P1P3": DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P1V1": DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P1V2": DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P1V3": DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P2P3": DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P2V1": DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P2V2": DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P2V3": DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P3V1": DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P3V2": DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/P3V3": DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/V1V2": DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/V1V3": DblType(),
    "ErrorStatistics/Components/PosVelErr/CorrCoefs/V2V3": DblType(),
    **_decorr_type("ErrorStatistics/Components/PosVelErr/PositionDecorr"),
    "ErrorStatistics/Components/RadarSensor/RangeBias": DblType(),
    "ErrorStatistics/Components/RadarSensor/ClockFreqSF": DblType(),
    "ErrorStatistics/Components/RadarSensor/TransmitFreqSF": DblType(),
    **_decorr_type("ErrorStatistics/Components/RadarSensor/RangeBiasDecorr"),
    "ErrorStatistics/Components/TropoError/TropoRangeVertical": DblType(),
    "ErrorStatistics/Components/TropoError/TropoRangeSlant": DblType(),
    **_decorr_type("ErrorStatistics/Components/TropoError/TropoRangeDecorr"),
    "ErrorStatistics/Components/IonoError/IonoRangeVertical": DblType(),
    "ErrorStatistics/Components/IonoError/IonoRangeRateVertical": DblType(),
    "ErrorStatistics/Components/IonoError/IonoRgRgRateCC": DblType(),
    **_decorr_type("ErrorStatistics/Components/IonoError/IonoRangeVertDecorr"),
    "ErrorStatistics/Unmodeled/Xrow": DblType(),
    "ErrorStatistics/Unmodeled/Ycol": DblType(),
    "ErrorStatistics/Unmodeled/XrowYcol": DblType(),
    **_decorr_type("ErrorStatistics/Unmodeled/UnmodeledDecorr/Xrow"),
    **_decorr_type("ErrorStatistics/Unmodeled/UnmodeledDecorr/Ycol"),
    "ErrorStatistics/AdditionalParms/Parameter": TxtType(),
}
TRANSCODERS |= {
    "Radiometric/NoiseLevel/NoiseLevelType": TxtType(),
    "Radiometric/NoiseLevel/NoisePoly": PolyCoef2dType(),
    "Radiometric/RCSSFPoly": PolyCoef2dType(),
    "Radiometric/SigmaZeroSFPoly": PolyCoef2dType(),
    "Radiometric/BetaZeroSFPoly": PolyCoef2dType(),
    "Radiometric/SigmaZeroSFIncidenceMap": TxtType(),
    "Radiometric/GammaZeroSFPoly": PolyCoef2dType(),
}
TRANSCODERS |= {
    "MatchInfo/NumMatchTypes": IntType(),
    "MatchInfo/MatchType/TypeID": TxtType(),
    "MatchInfo/MatchType/CurrentIndex": IntType(),
    "MatchInfo/MatchType/NumMatchCollections": IntType(),
    "MatchInfo/MatchType/MatchCollection/CoreName": TxtType(),
    "MatchInfo/MatchType/MatchCollection/MatchIndex": IntType(),
    "MatchInfo/MatchType/MatchCollection/Parameter": TxtType(),
}
TRANSCODERS |= {
    "Compression/J2K/Original/NumWaveletLevels": IntType(),
    "Compression/J2K/Original/NumBands": IntType(),
    "Compression/J2K/Original/LayerInfo/Layer/Bitrate": DblType(),
    "Compression/J2K/Parsed/NumWaveletLevels": IntType(),
    "Compression/J2K/Parsed/NumBands": IntType(),
    "Compression/J2K/Parsed/LayerInfo/Layer/Bitrate": DblType(),
}
TRANSCODERS |= {
    "DigitalElevationData/GeographicCoordinates/LongitudeDensity": DblType(),
    "DigitalElevationData/GeographicCoordinates/LatitudeDensity": DblType(),
    "DigitalElevationData/GeographicCoordinates/ReferenceOrigin": LatLonType(),
    "DigitalElevationData/Geopositioning/CoordinateSystemType": TxtType(),
    "DigitalElevationData/Geopositioning/GeodeticDatum": TxtType(),
    "DigitalElevationData/Geopositioning/ReferenceEllipsoid": TxtType(),
    "DigitalElevationData/Geopositioning/VerticalDatum": TxtType(),
    "DigitalElevationData/Geopositioning/SoundingDatum": TxtType(),
    "DigitalElevationData/Geopositioning/FalseOrigin": IntType(),
    "DigitalElevationData/Geopositioning/UTMGridZoneNumber": IntType(),
    "DigitalElevationData/PositionalAccuracy/NumRegions": IntType(),
    "DigitalElevationData/PositionalAccuracy/AbsoluteAccuracy/Horizontal": DblType(),
    "DigitalElevationData/PositionalAccuracy/AbsoluteAccuracy/Vertical": DblType(),
    "DigitalElevationData/PositionalAccuracy/PointToPointAccuracy/Horizontal": DblType(),
    "DigitalElevationData/PositionalAccuracy/PointToPointAccuracy/Vertical": DblType(),
    "DigitalElevationData/NullValue": IntType(),
}
TRANSCODERS |= {
    "ProductProcessing/ProcessingModule/ModuleName": ParameterType(),
    "ProductProcessing/ProcessingModule/ModuleParameter": ParameterType(),
}
TRANSCODERS |= {
    "Annotations/Annotation/Identifier": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/Csname": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/Csname": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/Datum/Spheroid/SpheriodName": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/Datum/Spheroid/SemiMajorAxis": DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/Datum/Spheroid/InverseFlattening": DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/PrimeMeridian/Name": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/PrimeMeridian/Longitude": DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/AngularUnit": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/GeographicCoordinateSystem/LinearUnit": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/Projection/ProjectionName": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/Parameter/ParameterName": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/Parameter/Value": DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/ProjectedCoordinateSystem/LinearUnit": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/Csname": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/Datum/Spheroid/SpheriodName": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/Datum/Spheroid/SemiMajorAxis": DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/Datum/Spheroid/InverseFlattening": DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/PrimeMeridian/Name": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/PrimeMeridian/Longitude": DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/AngularUnit": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeographicCoordinateSystem/LinearUnit": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/Csname": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/Datum/Spheroid/SpheriodName": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/Datum/Spheroid/SemiMajorAxis": DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/Datum/Spheroid/InverseFlattening": DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/PrimeMeridian/Name": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/PrimeMeridian/Longitude": DblType(),
    "Annotations/Annotation/SpatialReferenceSystem/GeocentricCoordinateSystem/LinearUnit": TxtType(),
    "Annotations/Annotation/SpatialReferenceSystem/AxisName": TxtType(),
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
