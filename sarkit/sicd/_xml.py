"""
Functions for interacting with SICD XML
"""

import copy
import re
from collections.abc import Sequence

import lxml.builder
import lxml.etree
import numpy as np
import numpy.polynomial.polynomial as npp
import numpy.typing as npt

import sarkit._xmlhelp as skxml
import sarkit.sicd._io as sicd_io
import sarkit.sicd.projection as ss_proj
from sarkit import _constants


# The following transcoders happen to share common implementation across several standards
@skxml.inheritdocstring
class TxtType(skxml.TxtType):
    pass


@skxml.inheritdocstring
class EnuType(skxml.EnuType):
    pass


@skxml.inheritdocstring
class BoolType(skxml.BoolType):
    pass


@skxml.inheritdocstring
class IntType(skxml.IntType):
    pass


@skxml.inheritdocstring
class DblType(skxml.DblType):
    pass


@skxml.inheritdocstring
class XdtType(skxml.XdtType):
    pass


@skxml.inheritdocstring
class RowColType(skxml.RowColType):
    pass


@skxml.inheritdocstring
class CmplxType(skxml.CmplxType):
    pass


@skxml.inheritdocstring
class XyzType(skxml.XyzType):
    pass


@skxml.inheritdocstring
class LatLonHaeType(skxml.LatLonHaeType):
    pass


@skxml.inheritdocstring
class LatLonType(skxml.LatLonType):
    pass


@skxml.inheritdocstring
class PolyType(skxml.PolyType):
    pass


@skxml.inheritdocstring
class Poly2dType(skxml.Poly2dType):
    pass


@skxml.inheritdocstring
class XyzPolyType(skxml.XyzPolyType):
    pass


@skxml.inheritdocstring
class MtxType(skxml.MtxType):
    pass


@skxml.inheritdocstring
class ParameterType(skxml.ParameterType):
    pass


class ImageCornersType(skxml.ListType):
    """
    Transcoder for SICD-like GeoData/ImageCorners XML parameter types.

    """

    def __init__(self) -> None:
        super().__init__("ICP", skxml.LatLonType())

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
        elem_ns = lxml.etree.QName(elem).namespace
        ns = f"{{{elem_ns}}}" if elem_ns else ""
        for label, coord in zip(labels, val):
            icp = lxml.etree.SubElement(
                elem, ns + self.sub_tag, attrib={"index": label}
            )
            self.sub_type.set_elem(icp, coord)


TRANSCODERS: dict[str, skxml.Type] = {
    "CollectionInfo/CollectorName": TxtType(),
    "CollectionInfo/IlluminatorName": TxtType(),
    "CollectionInfo/CoreName": TxtType(),
    "CollectionInfo/CollectType": TxtType(),
    "CollectionInfo/RadarMode/ModeType": TxtType(),
    "CollectionInfo/RadarMode/ModeID": TxtType(),
    "CollectionInfo/Classification": TxtType(),
    "CollectionInfo/InformationSecurityMarking": TxtType(),
    "CollectionInfo/CountryCode": TxtType(),
    "CollectionInfo/Parameter": ParameterType(),
}
TRANSCODERS |= {
    "ImageCreation/Application": TxtType(),
    "ImageCreation/DateTime": XdtType(),
    "ImageCreation/Site": TxtType(),
    "ImageCreation/Profile": TxtType(),
}
TRANSCODERS |= {
    "ImageData/PixelType": TxtType(),
    "ImageData/AmpTable": skxml.ListType("Amplitude", DblType(), index_start=0),
    "ImageData/NumRows": IntType(),
    "ImageData/NumCols": IntType(),
    "ImageData/FirstRow": IntType(),
    "ImageData/FirstCol": IntType(),
    "ImageData/FullImage/NumRows": IntType(),
    "ImageData/FullImage/NumCols": IntType(),
    "ImageData/SCPPixel": RowColType(),
    "ImageData/ValidData": skxml.ListType("Vertex", RowColType()),
}
TRANSCODERS |= {
    "GeoData/EarthModel": TxtType(),
    "GeoData/SCP/ECF": XyzType(),
    "GeoData/SCP/LLH": LatLonHaeType(),
    "GeoData/ImageCorners": ImageCornersType(),
    "GeoData/ValidData": skxml.ListType("Vertex", LatLonType()),
    "GeoData/GeoInfo/Desc": ParameterType(),
    "GeoData/GeoInfo/Point": LatLonType(),
    "GeoData/GeoInfo/Line": skxml.ListType("Endpoint", LatLonType()),
    "GeoData/GeoInfo/Polygon": skxml.ListType("Vertex", LatLonType()),
}
TRANSCODERS |= {
    "Grid/ImagePlane": TxtType(),
    "Grid/Type": TxtType(),
    "Grid/TimeCOAPoly": Poly2dType(),
}
for d in ("Row", "Col"):
    TRANSCODERS |= {
        f"Grid/{d}/UVectECF": XyzType(),
        f"Grid/{d}/SS": DblType(),
        f"Grid/{d}/ImpRespWid": DblType(),
        f"Grid/{d}/Sgn": IntType(),
        f"Grid/{d}/ImpRespBW": DblType(),
        f"Grid/{d}/KCtr": DblType(),
        f"Grid/{d}/DeltaK1": DblType(),
        f"Grid/{d}/DeltaK2": DblType(),
        f"Grid/{d}/DeltaKCOAPoly": Poly2dType(),
        f"Grid/{d}/WgtType/WindowName": TxtType(),
        f"Grid/{d}/WgtType/Parameter": ParameterType(),
        f"Grid/{d}/WgtFunct": skxml.ListType("Wgt", DblType()),
    }
TRANSCODERS |= {
    "Timeline/CollectStart": XdtType(),
    "Timeline/CollectDuration": DblType(),
    "Timeline/IPP/Set/TStart": DblType(),
    "Timeline/IPP/Set/TEnd": DblType(),
    "Timeline/IPP/Set/IPPStart": IntType(),
    "Timeline/IPP/Set/IPPEnd": IntType(),
    "Timeline/IPP/Set/IPPPoly": PolyType(),
}
TRANSCODERS |= {
    "Position/ARPPoly": XyzPolyType(),
    "Position/GRPPoly": XyzPolyType(),
    "Position/TxAPCPoly": XyzPolyType(),
    "Position/RcvAPC/RcvAPCPoly": XyzPolyType(),
}
TRANSCODERS |= {
    "RadarCollection/TxFrequency/Min": DblType(),
    "RadarCollection/TxFrequency/Max": DblType(),
    "RadarCollection/RefFreqIndex": IntType(),
    "RadarCollection/Waveform/WFParameters/TxPulseLength": DblType(),
    "RadarCollection/Waveform/WFParameters/TxRFBandwidth": DblType(),
    "RadarCollection/Waveform/WFParameters/TxFreqStart": DblType(),
    "RadarCollection/Waveform/WFParameters/TxFMRate": DblType(),
    "RadarCollection/Waveform/WFParameters/RcvDemodType": TxtType(),
    "RadarCollection/Waveform/WFParameters/RcvWindowLength": DblType(),
    "RadarCollection/Waveform/WFParameters/ADCSampleRate": DblType(),
    "RadarCollection/Waveform/WFParameters/RcvIFBandwidth": DblType(),
    "RadarCollection/Waveform/WFParameters/RcvFreqStart": DblType(),
    "RadarCollection/Waveform/WFParameters/RcvFMRate": DblType(),
    "RadarCollection/TxPolarization": TxtType(),
    "RadarCollection/TxSequence/TxStep/WFIndex": IntType(),
    "RadarCollection/TxSequence/TxStep/TxPolarization": TxtType(),
    "RadarCollection/RcvChannels/ChanParameters/TxRcvPolarization": TxtType(),
    "RadarCollection/RcvChannels/ChanParameters/RcvAPCIndex": IntType(),
    "RadarCollection/Area/Corner": skxml.ListType(
        "ACP", LatLonHaeType(), include_size_attr=False
    ),
    "RadarCollection/Area/Plane/RefPt/ECF": XyzType(),
    "RadarCollection/Area/Plane/RefPt/Line": DblType(),
    "RadarCollection/Area/Plane/RefPt/Sample": DblType(),
    "RadarCollection/Area/Plane/XDir/UVectECF": XyzType(),
    "RadarCollection/Area/Plane/XDir/LineSpacing": DblType(),
    "RadarCollection/Area/Plane/XDir/NumLines": IntType(),
    "RadarCollection/Area/Plane/XDir/FirstLine": IntType(),
    "RadarCollection/Area/Plane/YDir/UVectECF": XyzType(),
    "RadarCollection/Area/Plane/YDir/SampleSpacing": DblType(),
    "RadarCollection/Area/Plane/YDir/NumSamples": IntType(),
    "RadarCollection/Area/Plane/YDir/FirstSample": IntType(),
    "RadarCollection/Area/Plane/SegmentList/Segment/StartLine": IntType(),
    "RadarCollection/Area/Plane/SegmentList/Segment/StartSample": IntType(),
    "RadarCollection/Area/Plane/SegmentList/Segment/EndLine": IntType(),
    "RadarCollection/Area/Plane/SegmentList/Segment/EndSample": IntType(),
    "RadarCollection/Area/Plane/SegmentList/Segment/Identifier": TxtType(),
    "RadarCollection/Area/Plane/Orientation": TxtType(),
    "RadarCollection/Parameter": ParameterType(),
}
TRANSCODERS |= {
    "ImageFormation/RcvChanProc/NumChanProc": IntType(),
    "ImageFormation/RcvChanProc/PRFScaleFactor": DblType(),
    "ImageFormation/RcvChanProc/ChanIndex": IntType(),
    "ImageFormation/TxRcvPolarizationProc": TxtType(),
    "ImageFormation/TStartProc": DblType(),
    "ImageFormation/TEndProc": DblType(),
    "ImageFormation/TxFrequencyProc/MinProc": DblType(),
    "ImageFormation/TxFrequencyProc/MaxProc": DblType(),
    "ImageFormation/SegmentIdentifier": TxtType(),
    "ImageFormation/ImageFormAlgo": TxtType(),
    "ImageFormation/STBeamComp": TxtType(),
    "ImageFormation/ImageBeamComp": TxtType(),
    "ImageFormation/AzAutofocus": TxtType(),
    "ImageFormation/RgAutofocus": TxtType(),
    "ImageFormation/Processing/Type": TxtType(),
    "ImageFormation/Processing/Applied": BoolType(),
    "ImageFormation/Processing/Parameter": ParameterType(),
    "ImageFormation/PolarizationCalibration/DistortCorrectionApplied": BoolType(),
    "ImageFormation/PolarizationCalibration/Distortion/CalibrationDate": XdtType(),
    "ImageFormation/PolarizationCalibration/Distortion/A": DblType(),
    "ImageFormation/PolarizationCalibration/Distortion/F1": CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/Q1": CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/Q2": CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/F2": CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/Q3": CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/Q4": CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/GainErrorA": DblType(),
    "ImageFormation/PolarizationCalibration/Distortion/GainErrorF1": DblType(),
    "ImageFormation/PolarizationCalibration/Distortion/GainErrorF2": DblType(),
    "ImageFormation/PolarizationCalibration/Distortion/PhaseErrorF1": DblType(),
    "ImageFormation/PolarizationCalibration/Distortion/PhaseErrorF2": DblType(),
}
TRANSCODERS |= {
    "SCPCOA/SCPTime": DblType(),
    "SCPCOA/ARPPos": XyzType(),
    "SCPCOA/ARPVel": XyzType(),
    "SCPCOA/ARPAcc": XyzType(),
    "SCPCOA/SideOfTrack": TxtType(),
    "SCPCOA/SlantRange": DblType(),
    "SCPCOA/GroundRange": DblType(),
    "SCPCOA/DopplerConeAng": DblType(),
    "SCPCOA/GrazeAng": DblType(),
    "SCPCOA/IncidenceAng": DblType(),
    "SCPCOA/TwistAng": DblType(),
    "SCPCOA/SlopeAng": DblType(),
    "SCPCOA/AzimAng": DblType(),
    "SCPCOA/LayoverAng": DblType(),
    "SCPCOA/Bistatic/BistaticAng": DblType(),
    "SCPCOA/Bistatic/BistaticAngRate": DblType(),
}
for d in ("Tx", "Rcv"):
    TRANSCODERS |= {
        f"SCPCOA/Bistatic/{d}Platform/Time": DblType(),
        f"SCPCOA/Bistatic/{d}Platform/Pos": XyzType(),
        f"SCPCOA/Bistatic/{d}Platform/Vel": XyzType(),
        f"SCPCOA/Bistatic/{d}Platform/Acc": XyzType(),
        f"SCPCOA/Bistatic/{d}Platform/SideOfTrack": TxtType(),
        f"SCPCOA/Bistatic/{d}Platform/SlantRange": DblType(),
        f"SCPCOA/Bistatic/{d}Platform/GroundRange": DblType(),
        f"SCPCOA/Bistatic/{d}Platform/DopplerConeAng": DblType(),
        f"SCPCOA/Bistatic/{d}Platform/GrazeAng": DblType(),
        f"SCPCOA/Bistatic/{d}Platform/IncidenceAng": DblType(),
        f"SCPCOA/Bistatic/{d}Platform/AzimAng": DblType(),
    }
TRANSCODERS |= {
    "Radiometric/NoiseLevel/NoiseLevelType": TxtType(),
    "Radiometric/NoiseLevel/NoisePoly": Poly2dType(),
    "Radiometric/RCSSFPoly": Poly2dType(),
    "Radiometric/SigmaZeroSFPoly": Poly2dType(),
    "Radiometric/BetaZeroSFPoly": Poly2dType(),
    "Radiometric/GammaZeroSFPoly": Poly2dType(),
}
for a in ("Tx", "Rcv", "TwoWay"):
    TRANSCODERS |= {
        f"Antenna/{a}/XAxisPoly": XyzPolyType(),
        f"Antenna/{a}/YAxisPoly": XyzPolyType(),
        f"Antenna/{a}/FreqZero": DblType(),
        f"Antenna/{a}/EB/DCXPoly": PolyType(),
        f"Antenna/{a}/EB/DCYPoly": PolyType(),
        f"Antenna/{a}/Array/GainPoly": Poly2dType(),
        f"Antenna/{a}/Array/PhasePoly": Poly2dType(),
        f"Antenna/{a}/Elem/GainPoly": Poly2dType(),
        f"Antenna/{a}/Elem/PhasePoly": Poly2dType(),
        f"Antenna/{a}/GainBSPoly": PolyType(),
        f"Antenna/{a}/EBFreqShift": BoolType(),
        f"Antenna/{a}/MLFreqDilation": BoolType(),
    }


def _decorr_type(xml_path):
    return {f"{xml_path}/{x}": DblType() for x in ("CorrCoefZero", "DecorrRate")}


TRANSCODERS |= {
    "ErrorStatistics/CompositeSCP/Rg": DblType(),
    "ErrorStatistics/CompositeSCP/Az": DblType(),
    "ErrorStatistics/CompositeSCP/RgAz": DblType(),
    "ErrorStatistics/BistaticCompositeSCP/RAvg": DblType(),
    "ErrorStatistics/BistaticCompositeSCP/RdotAvg": DblType(),
    "ErrorStatistics/BistaticCompositeSCP/RAvgRdotAvg": DblType(),
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
    "ErrorStatistics/BistaticComponents/PosVelErr/TxFrame": TxtType(),
    "ErrorStatistics/BistaticComponents/PosVelErr/TxPVCov": MtxType((6, 6)),
    "ErrorStatistics/BistaticComponents/PosVelErr/RcvFrame": TxtType(),
    "ErrorStatistics/BistaticComponents/PosVelErr/RcvPVCov": MtxType((6, 6)),
    "ErrorStatistics/BistaticComponents/PosVelErr/TxRcvPVXCov": MtxType((6, 6)),
    "ErrorStatistics/BistaticComponents/RadarSensor/TxRcvTimeFreq": MtxType((4, 4)),
    **_decorr_type(
        "ErrorStatistics/BistaticComponents/RadarSensor/TxRcvTimeFreqDecorr/TxTimeDecorr"
    ),
    **_decorr_type(
        "ErrorStatistics/BistaticComponents/RadarSensor/TxRcvTimeFreqDecorr/TxClockFreqDecorr"
    ),
    **_decorr_type(
        "ErrorStatistics/BistaticComponents/RadarSensor/TxRcvTimeFreqDecorr/RcvTimeDecorr"
    ),
    **_decorr_type(
        "ErrorStatistics/BistaticComponents/RadarSensor/TxRcvTimeFreqDecorr/RcvClockFreqDecorr"
    ),
    "ErrorStatistics/BistaticComponents/AtmosphericError/TxSCP": DblType(),
    "ErrorStatistics/BistaticComponents/AtmosphericError/RcvSCP": DblType(),
    "ErrorStatistics/BistaticComponents/AtmosphericError/TxRcvCC": DblType(),
    "ErrorStatistics/Unmodeled/Xrow": DblType(),
    "ErrorStatistics/Unmodeled/Ycol": DblType(),
    "ErrorStatistics/Unmodeled/XrowYcol": DblType(),
    **_decorr_type("ErrorStatistics/Unmodeled/UnmodeledDecorr/Xrow"),
    **_decorr_type("ErrorStatistics/Unmodeled/UnmodeledDecorr/Ycol"),
    "ErrorStatistics/AdditionalParms/Parameter": ParameterType(),
    "ErrorStatistics/AdjustableParameterOffsets/ARPPosSCPCOA": XyzType(),
    "ErrorStatistics/AdjustableParameterOffsets/ARPVel": XyzType(),
    "ErrorStatistics/AdjustableParameterOffsets/TxTimeSCPCOA": DblType(),
    "ErrorStatistics/AdjustableParameterOffsets/RcvTimeSCPCOA": DblType(),
    "ErrorStatistics/AdjustableParameterOffsets/APOError": MtxType((8, 8)),
    "ErrorStatistics/AdjustableParameterOffsets/CompositeSCP/Rg": DblType(),
    "ErrorStatistics/AdjustableParameterOffsets/CompositeSCP/Az": DblType(),
    "ErrorStatistics/AdjustableParameterOffsets/CompositeSCP/RgAz": DblType(),
}
for p in ("Tx", "Rcv"):
    TRANSCODERS |= {
        f"ErrorStatistics/BistaticAdjustableParameterOffsets/{p}Platform/APCPosSCPCOA": XyzType(),
        f"ErrorStatistics/BistaticAdjustableParameterOffsets/{p}Platform/APCVel": XyzType(),
        f"ErrorStatistics/BistaticAdjustableParameterOffsets/{p}Platform/TimeSCPCOA": DblType(),
        f"ErrorStatistics/BistaticAdjustableParameterOffsets/{p}Platform/ClockFreqSF": DblType(),
    }
TRANSCODERS |= {
    "ErrorStatistics/BistaticAdjustableParameterOffsets/APOError": MtxType((16, 16)),
    "ErrorStatistics/BistaticAdjustableParameterOffsets/BistaticCompositeSCP/RAvg": DblType(),
    "ErrorStatistics/BistaticAdjustableParameterOffsets/BistaticCompositeSCP/RdotAvg": DblType(),
    "ErrorStatistics/BistaticAdjustableParameterOffsets/BistaticCompositeSCP/RAvgRdotAvg": DblType(),
}
TRANSCODERS |= {
    "MatchInfo/NumMatchTypes": IntType(),
    "MatchInfo/MatchType/TypeID": TxtType(),
    "MatchInfo/MatchType/CurrentIndex": IntType(),
    "MatchInfo/MatchType/NumMatchCollections": IntType(),
    "MatchInfo/MatchType/MatchCollection/CoreName": TxtType(),
    "MatchInfo/MatchType/MatchCollection/MatchIndex": IntType(),
    "MatchInfo/MatchType/MatchCollection/Parameter": ParameterType(),
}
TRANSCODERS |= {
    "RgAzComp/AzSF": DblType(),
    "RgAzComp/KazPoly": PolyType(),
}
TRANSCODERS |= {
    "PFA/FPN": XyzType(),
    "PFA/IPN": XyzType(),
    "PFA/PolarAngRefTime": DblType(),
    "PFA/PolarAngPoly": PolyType(),
    "PFA/SpatialFreqSFPoly": PolyType(),
    "PFA/Krg1": DblType(),
    "PFA/Krg2": DblType(),
    "PFA/Kaz1": DblType(),
    "PFA/Kaz2": DblType(),
    "PFA/STDeskew/Applied": BoolType(),
    "PFA/STDeskew/STDSPhasePoly": Poly2dType(),
}
TRANSCODERS |= {
    "RMA/RMAlgoType": TxtType(),
    "RMA/ImageType": TxtType(),
    "RMA/RMAT/PosRef": XyzType(),
    "RMA/RMAT/VelRef": XyzType(),
    "RMA/RMAT/DopConeAngRef": DblType(),
    "RMA/RMCR/PosRef": XyzType(),
    "RMA/RMCR/VelRef": XyzType(),
    "RMA/RMCR/DopConeAngRef": DblType(),
    "RMA/INCA/TimeCAPoly": PolyType(),
    "RMA/INCA/R_CA_SCP": DblType(),
    "RMA/INCA/FreqZero": DblType(),
    "RMA/INCA/DRateSFPoly": Poly2dType(),
    "RMA/INCA/DopCentroidPoly": Poly2dType(),
    "RMA/INCA/DopCentroidCOA": BoolType(),
}

# Polynomial subelements
TRANSCODERS.update(
    {
        f"{p}/{coord}": PolyType()
        for p, v in TRANSCODERS.items()
        if isinstance(v, skxml.XyzPolyType)
        for coord in "XYZ"
    }
)
TRANSCODERS.update(
    {
        f"{p}/Coef": DblType()
        for p, v in TRANSCODERS.items()
        if isinstance(v, skxml.PolyNdType)
    }
)

# Matrix subelements
TRANSCODERS.update(
    {
        f"{p}/Entry": DblType()
        for p, v in TRANSCODERS.items()
        if isinstance(v, skxml.MtxType)
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
    XmlHelper for Sensor Independent Complex Data (SICD).

    """

    _transcoders_ = TRANSCODERS

    def _get_simple_path(self, elem):
        return re.sub(r"(GeoInfo/)+", "GeoInfo/", super()._get_simple_path(elem))


def compute_scp_coa(sicd_xmltree: lxml.etree.ElementTree) -> lxml.etree.ElementTree:
    """Return a SICD/SCPCOA XML containing parameters computed from other metadata.

    The namespace of the new SICD/SCPCOA element is retained from ``sicd_xmltree``.

    Parameters
    ----------
    sicd_xmltree : lxml.etree.ElementTree
        SICD XML ElementTree

    Returns
    -------
    lxml.etree.Element
        New SICD/SCPCOA XML element
    """
    xmlhelp = XmlHelper(copy.deepcopy(sicd_xmltree))
    version_ns = lxml.etree.QName(sicd_xmltree.getroot()).namespace
    sicd_versions = list(sicd_io.VERSION_INFO)
    pre_1_4 = sicd_versions.index(version_ns) < sicd_versions.index("urn:SICD:1.4.0")

    # COA Parameters for All Images
    scpcoa_params = {}
    t_coa = xmlhelp.load("./{*}Grid/{*}TimeCOAPoly")[0, 0]
    scpcoa_params["SCPTime"] = t_coa
    scp = xmlhelp.load("./{*}GeoData/{*}SCP/{*}ECF")

    arp_poly = xmlhelp.load("./{*}Position/{*}ARPPoly")
    arp_coa = npp.polyval(t_coa, arp_poly).squeeze()
    scpcoa_params["ARPPos"] = arp_coa
    varp_coa = npp.polyval(t_coa, npp.polyder(arp_poly, m=1)).squeeze()
    scpcoa_params["ARPVel"] = varp_coa
    aarp_coa = npp.polyval(t_coa, npp.polyder(arp_poly, m=2)).squeeze()
    scpcoa_params["ARPAcc"] = aarp_coa

    r_coa = np.linalg.norm(scp - arp_coa)
    scpcoa_params["SlantRange"] = r_coa
    arp_dec_coa = np.linalg.norm(arp_coa)
    u_arp_coa = arp_coa / arp_dec_coa
    scp_dec = np.linalg.norm(scp)
    u_scp = scp / scp_dec
    ea_coa = np.arccos(np.dot(u_arp_coa, u_scp))
    rg_coa = scp_dec * ea_coa
    scpcoa_params["GroundRange"] = rg_coa

    vm_coa = np.linalg.norm(varp_coa)
    u_varp_coa = varp_coa / vm_coa
    u_los_coa = (scp - arp_coa) / r_coa
    left_coa = np.cross(u_arp_coa, u_varp_coa)
    dca_coa = np.arccos(np.dot(u_varp_coa, u_los_coa))
    scpcoa_params["DopplerConeAng"] = np.rad2deg(dca_coa)
    side_of_track = "L" if np.dot(left_coa, u_los_coa) > 0 else "R"
    scpcoa_params["SideOfTrack"] = side_of_track
    look = 1 if np.dot(left_coa, u_los_coa) > 0 else -1

    scp_lon = xmlhelp.load("./{*}GeoData/{*}SCP/{*}LLH/{*}Lon")
    scp_lat = xmlhelp.load("./{*}GeoData/{*}SCP/{*}LLH/{*}Lat")
    u_gpz = np.array(
        [
            np.cos(np.deg2rad(scp_lon)) * np.cos(np.deg2rad(scp_lat)),
            np.sin(np.deg2rad(scp_lon)) * np.cos(np.deg2rad(scp_lat)),
            np.sin(np.deg2rad(scp_lat)),
        ]
    )
    arp_gpz_coa = np.dot(arp_coa - scp, u_gpz)
    aetp_coa = arp_coa - u_gpz * arp_gpz_coa
    arp_gpx_coa = np.linalg.norm(aetp_coa - scp)
    u_gpx = (aetp_coa - scp) / arp_gpx_coa
    u_gpy = np.cross(u_gpz, u_gpx)

    cos_graz = arp_gpx_coa / r_coa
    sin_graz = arp_gpz_coa / r_coa
    graz = np.arccos(cos_graz) if pre_1_4 else np.arcsin(sin_graz)
    scpcoa_params["GrazeAng"] = np.rad2deg(graz)
    incd = 90.0 - np.rad2deg(graz)
    scpcoa_params["IncidenceAng"] = incd

    spz = look * np.cross(u_varp_coa, u_los_coa)
    u_spz = spz / np.linalg.norm(spz)
    # u_spx intentionally omitted
    # u_spy intentionally omitted

    # arp/varp in slant plane coordinates intentionally omitted

    slope = np.arccos(np.dot(u_gpz, u_spz))
    scpcoa_params["SlopeAng"] = np.rad2deg(slope)

    u_east = np.array([-np.sin(np.deg2rad(scp_lon)), np.cos(np.deg2rad(scp_lon)), 0.0])
    u_north = np.cross(u_gpz, u_east)
    az_north = np.dot(u_north, u_gpx)
    az_east = np.dot(u_east, u_gpx)
    azim = np.arctan2(az_east, az_north)
    scpcoa_params["AzimAng"] = np.rad2deg(azim) % 360

    cos_slope = np.cos(slope)  # this symbol seems to be undefined in SICD Vol 1
    lodir_coa = u_gpz - u_spz / cos_slope
    lo_north = np.dot(u_north, lodir_coa)
    lo_east = np.dot(u_east, lodir_coa)
    layover = np.arctan2(lo_east, lo_north)
    scpcoa_params["LayoverAng"] = np.rad2deg(layover) % 360

    # uZI intentionally omitted

    twst = -np.arcsin(np.dot(u_gpy, u_spz))
    scpcoa_params["TwistAng"] = np.rad2deg(twst)

    # Build new XML element
    em = lxml.builder.ElementMaker(namespace=version_ns, nsmap={None: version_ns})
    sicd = em.SICD(em.SCPCOA())
    new_scpcoa_elem = sicd[0]
    xmlhelp_out = XmlHelper(sicd.getroottree())

    def _append_elems(parent, d):
        element_path = xmlhelp_out.element_tree.getelementpath(parent)
        no_ns_path = re.sub(r"\{.*?\}|\[.*?\]", "", element_path)
        for name, val in sorted(
            d.items(), key=lambda x: list(TRANSCODERS).index(f"{no_ns_path}/{x[0]}")
        ):
            elem = em(name)
            parent.append(elem)
            xmlhelp_out.set_elem(elem, val)

    _append_elems(new_scpcoa_elem, scpcoa_params)

    # Additional COA Parameters for Bistatic Images
    params = ss_proj.MetadataParams.from_xml(sicd_xmltree)
    if not pre_1_4 and not params.is_monostatic():
        assert params.Xmt_Poly is not None
        assert params.Rcv_Poly is not None
        tx_coa = t_coa - (1 / _constants.speed_of_light) * np.linalg.norm(
            npp.polyval(t_coa, params.Xmt_Poly) - scp
        )
        tr_coa = t_coa + (1 / _constants.speed_of_light) * np.linalg.norm(
            npp.polyval(t_coa, params.Rcv_Poly) - scp
        )

        xmt_coa = npp.polyval(tx_coa, params.Xmt_Poly)
        vxmt_coa = npp.polyval(tx_coa, npp.polyder(params.Xmt_Poly, m=1))
        axmt_coa = npp.polyval(tx_coa, npp.polyder(params.Xmt_Poly, m=2))
        r_xmt_scp = np.linalg.norm(xmt_coa - scp)
        u_xmt_coa = (xmt_coa - scp) / r_xmt_scp

        rdot_xmt_scp = np.dot(u_xmt_coa, vxmt_coa)
        u_xmt_dot_coa = (vxmt_coa - rdot_xmt_scp * u_xmt_coa) / r_xmt_scp

        rcv_coa = npp.polyval(tr_coa, params.Rcv_Poly)
        vrcv_coa = npp.polyval(tr_coa, npp.polyder(params.Rcv_Poly, m=1))
        arcv_coa = npp.polyval(tr_coa, npp.polyder(params.Rcv_Poly, m=2))
        r_rcv_scp = np.linalg.norm(rcv_coa - scp)
        u_rcv_coa = (rcv_coa - scp) / r_rcv_scp

        rdot_rcv_scp = np.dot(u_rcv_coa, vrcv_coa)
        u_rcv_dot_coa = (vrcv_coa - rdot_rcv_scp * u_rcv_coa) / r_rcv_scp

        bp_coa = 0.5 * (u_xmt_coa + u_rcv_coa)
        bpdot_coa = 0.5 * (u_xmt_dot_coa + u_rcv_dot_coa)

        bp_mag_coa = np.linalg.norm(bp_coa)
        bistat_ang_coa = 2.0 * np.arccos(bp_mag_coa)

        if bp_mag_coa in (0.0, 1.0):
            bistat_ang_rate_coa = 0.0
        else:
            bistat_ang_rate_coa = (
                (-180 / np.pi)
                * (4 / np.sin(bistat_ang_coa))
                * np.dot(bp_coa, bpdot_coa)
            )

        def _steps_10_to_15(xmt_coa, vxmt_coa, u_xmt_coa, r_xmt_scp):
            xmt_dec = np.linalg.norm(xmt_coa)
            u_ec_xmt_coa = xmt_coa / xmt_dec
            ea_xmt_coa = np.arccos(np.dot(u_ec_xmt_coa, u_scp))
            rg_xmt_scp = scp_dec * ea_xmt_coa

            left_xmt = np.cross(u_ec_xmt_coa, vxmt_coa)
            side_of_track_xmt = "L" if np.dot(left_xmt, u_xmt_coa) < 0 else "R"

            vxmt_m = np.linalg.norm(vxmt_coa)
            dca_xmt = np.arccos(-rdot_xmt_scp / vxmt_m)

            xmt_gpz_coa = np.dot((xmt_coa - scp), u_gpz)
            xmt_etp_coa = xmt_coa - xmt_gpz_coa * u_gpz
            u_gpx_x = (xmt_etp_coa - scp) / np.linalg.norm(xmt_etp_coa - scp)

            graz_xmt = np.arcsin(xmt_gpz_coa / r_xmt_scp)
            incd_xmt = 90 - np.rad2deg(graz_xmt)

            az_xmt_n = np.dot(u_north, u_gpx_x)
            az_xmt_e = np.dot(u_east, u_gpx_x)
            azim_xmt = np.arctan2(az_xmt_e, az_xmt_n)

            return {
                "SideOfTrack": side_of_track_xmt,
                "SlantRange": r_xmt_scp,
                "GroundRange": rg_xmt_scp,
                "DopplerConeAng": np.rad2deg(dca_xmt),
                "GrazeAng": np.rad2deg(graz_xmt),
                "IncidenceAng": incd_xmt,
                "AzimAng": np.rad2deg(azim_xmt) % 360,
            }

        bistat_elem = em.Bistatic()
        new_scpcoa_elem.append(bistat_elem)
        _append_elems(
            bistat_elem,
            {
                "BistaticAng": np.rad2deg(bistat_ang_coa),
                "BistaticAngRate": bistat_ang_rate_coa,
            },
        )
        tx_platform_elem = em.TxPlatform()
        bistat_elem.append(tx_platform_elem)
        _append_elems(
            tx_platform_elem,
            {
                "Time": tx_coa,
                "Pos": xmt_coa,
                "Vel": vxmt_coa,
                "Acc": axmt_coa,
                **_steps_10_to_15(xmt_coa, vxmt_coa, u_xmt_coa, r_xmt_scp),
            },
        )
        rcv_platform_elem = em.RcvPlatform()
        bistat_elem.append(rcv_platform_elem)
        _append_elems(
            rcv_platform_elem,
            {
                "Time": tr_coa,
                "Pos": rcv_coa,
                "Vel": vrcv_coa,
                "Acc": arcv_coa,
                **_steps_10_to_15(rcv_coa, vrcv_coa, u_rcv_coa, r_rcv_scp),
            },
        )

    return new_scpcoa_elem
