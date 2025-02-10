"""
========
SICD XML
========

Functions from SICD Volume 1 Design & Implementation Description Document.

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
import sarkit.constants
import sarkit.standards.sicd.io
import sarkit.standards.sicd.projection as ss_proj


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


class MtxType(skxml.Type):
    """
    Transcoder for MTX XML parameter types containing a matrix.

    Attributes
    ----------
    shape : 2-tuple of ints
        Expected shape of the matrix.

    """

    def __init__(self, shape) -> None:
        self.shape = shape

    def parse_elem(self, elem: lxml.etree.Element) -> npt.NDArray:
        """Returns an array containing the matrix encoded in ``elem``."""
        shape = tuple(int(elem.get(f"size{d}")) for d in (1, 2))
        if self.shape != shape:
            raise ValueError(f"elem {shape=} does not match expected {self.shape}")
        val = np.zeros(shape)
        for entry in elem:
            val[*[int(entry.get(f"index{x}")) - 1 for x in (1, 2)]] = float(entry.text)
        return val

    def set_elem(self, elem: lxml.etree.Element, val: npt.ArrayLike) -> None:
        """Set ``elem`` node using ``val``.

        Parameters
        ----------
        elem : lxml.etree.Element
            XML element to set
        val : array_like
            matrix of shape= ``shape``

        """
        mtx = np.asarray(val)
        if self.shape != mtx.shape:
            raise ValueError(f"{mtx.shape=} does not match expected {self.shape}")
        elem[:] = []
        elem_ns = lxml.etree.QName(elem).namespace
        ns = f"{{{elem_ns}}}" if elem_ns else ""
        for d, nd in zip((1, 2), mtx.shape, strict=True):
            elem.set(f"size{d}", str(nd))
        for indices, entry in np.ndenumerate(mtx):
            attribs = {f"index{d + 1}": str(c + 1) for d, c in enumerate(indices)}
            lxml.etree.SubElement(elem, ns + "Entry", attrib=attribs).text = str(entry)


TRANSCODERS: dict[str, skxml.Type] = {
    "CollectionInfo/CollectorName": skxml.TxtType(),
    "CollectionInfo/IlluminatorName": skxml.TxtType(),
    "CollectionInfo/CoreName": skxml.TxtType(),
    "CollectionInfo/CollectType": skxml.TxtType(),
    "CollectionInfo/RadarMode/ModeType": skxml.TxtType(),
    "CollectionInfo/RadarMode/ModeID": skxml.TxtType(),
    "CollectionInfo/Classification": skxml.TxtType(),
    "CollectionInfo/InformationSecurityMarking": skxml.TxtType(),
    "CollectionInfo/CountryCode": skxml.TxtType(),
    "CollectionInfo/Parameter": skxml.ParameterType(),
}
TRANSCODERS |= {
    "ImageCreation/Application": skxml.TxtType(),
    "ImageCreation/DateTime": skxml.XdtType(),
    "ImageCreation/Site": skxml.TxtType(),
    "ImageCreation/Profile": skxml.TxtType(),
}
TRANSCODERS |= {
    "ImageData/PixelType": skxml.TxtType(),
    "ImageData/AmpTable": skxml.ListType("Amplitude", skxml.DblType(), index_start=0),
    "ImageData/NumRows": skxml.IntType(),
    "ImageData/NumCols": skxml.IntType(),
    "ImageData/FirstRow": skxml.IntType(),
    "ImageData/FirstCol": skxml.IntType(),
    "ImageData/FullImage/NumRows": skxml.IntType(),
    "ImageData/FullImage/NumCols": skxml.IntType(),
    "ImageData/SCPPixel": skxml.RowColType(),
    "ImageData/ValidData": skxml.ListType("Vertex", skxml.RowColType()),
}
TRANSCODERS |= {
    "GeoData/EarthModel": skxml.TxtType(),
    "GeoData/SCP/ECF": skxml.XyzType(),
    "GeoData/SCP/LLH": skxml.LatLonHaeType(),
    "GeoData/ImageCorners": ImageCornersType(),
    "GeoData/ValidData": skxml.ListType("Vertex", skxml.LatLonType()),
    "GeoData/GeoInfo/Desc": skxml.ParameterType(),
    "GeoData/GeoInfo/Point": skxml.LatLonType(),
    "GeoData/GeoInfo/Line": skxml.ListType("Endpoint", skxml.LatLonType()),
    "GeoData/GeoInfo/Polygon": skxml.ListType("Vertex", skxml.LatLonType()),
}
TRANSCODERS |= {
    "Grid/ImagePlane": skxml.TxtType(),
    "Grid/Type": skxml.TxtType(),
    "Grid/TimeCOAPoly": skxml.Poly2dType(),
}
for d in ("Row", "Col"):
    TRANSCODERS |= {
        f"Grid/{d}/UVectECF": skxml.XyzType(),
        f"Grid/{d}/SS": skxml.DblType(),
        f"Grid/{d}/ImpRespWid": skxml.DblType(),
        f"Grid/{d}/Sgn": skxml.IntType(),
        f"Grid/{d}/ImpRespBW": skxml.DblType(),
        f"Grid/{d}/KCtr": skxml.DblType(),
        f"Grid/{d}/DeltaK1": skxml.DblType(),
        f"Grid/{d}/DeltaK2": skxml.DblType(),
        f"Grid/{d}/DeltaKCOAPoly": skxml.Poly2dType(),
        f"Grid/{d}/WgtType/WindowName": skxml.TxtType(),
        f"Grid/{d}/WgtType/Parameter": skxml.ParameterType(),
        f"Grid/{d}/WgtFunct": skxml.ListType("Wgt", skxml.DblType()),
    }
TRANSCODERS |= {
    "Timeline/CollectStart": skxml.XdtType(),
    "Timeline/CollectDuration": skxml.DblType(),
    "Timeline/IPP/Set/TStart": skxml.DblType(),
    "Timeline/IPP/Set/TEnd": skxml.DblType(),
    "Timeline/IPP/Set/IPPStart": skxml.IntType(),
    "Timeline/IPP/Set/IPPEnd": skxml.IntType(),
    "Timeline/IPP/Set/IPPPoly": skxml.PolyType(),
}
TRANSCODERS |= {
    "Position/ARPPoly": skxml.XyzPolyType(),
    "Position/GRPPoly": skxml.XyzPolyType(),
    "Position/TxAPCPoly": skxml.XyzPolyType(),
    "Position/RcvAPC/RcvAPCPoly": skxml.XyzPolyType(),
}
TRANSCODERS |= {
    "RadarCollection/TxFrequency/Min": skxml.DblType(),
    "RadarCollection/TxFrequency/Max": skxml.DblType(),
    "RadarCollection/RefFreqIndex": skxml.IntType(),
    "RadarCollection/Waveform/WFParameters/TxPulseLength": skxml.DblType(),
    "RadarCollection/Waveform/WFParameters/TxRFBandwidth": skxml.DblType(),
    "RadarCollection/Waveform/WFParameters/TxFreqStart": skxml.DblType(),
    "RadarCollection/Waveform/WFParameters/TxFMRate": skxml.DblType(),
    "RadarCollection/Waveform/WFParameters/RcvDemodType": skxml.TxtType(),
    "RadarCollection/Waveform/WFParameters/RcvWindowLength": skxml.DblType(),
    "RadarCollection/Waveform/WFParameters/ADCSampleRate": skxml.DblType(),
    "RadarCollection/Waveform/WFParameters/RcvIFBandwidth": skxml.DblType(),
    "RadarCollection/Waveform/WFParameters/RcvFreqStart": skxml.DblType(),
    "RadarCollection/Waveform/WFParameters/RcvFMRate": skxml.DblType(),
    "RadarCollection/TxPolarization": skxml.TxtType(),
    "RadarCollection/TxSequence/TxStep/WFIndex": skxml.IntType(),
    "RadarCollection/TxSequence/TxStep/TxPolarization": skxml.TxtType(),
    "RadarCollection/RcvChannels/ChanParameters/TxRcvPolarization": skxml.TxtType(),
    "RadarCollection/RcvChannels/ChanParameters/RcvAPCIndex": skxml.IntType(),
    "RadarCollection/Area/Corner": skxml.ListType(
        "ACP", skxml.LatLonHaeType(), include_size_attr=False
    ),
    "RadarCollection/Area/Plane/RefPt/ECF": skxml.XyzType(),
    "RadarCollection/Area/Plane/RefPt/Line": skxml.DblType(),
    "RadarCollection/Area/Plane/RefPt/Sample": skxml.DblType(),
    "RadarCollection/Area/Plane/XDir/UVectECF": skxml.XyzType(),
    "RadarCollection/Area/Plane/XDir/LineSpacing": skxml.DblType(),
    "RadarCollection/Area/Plane/XDir/NumLines": skxml.IntType(),
    "RadarCollection/Area/Plane/XDir/FirstLine": skxml.IntType(),
    "RadarCollection/Area/Plane/YDir/UVectECF": skxml.XyzType(),
    "RadarCollection/Area/Plane/YDir/SampleSpacing": skxml.DblType(),
    "RadarCollection/Area/Plane/YDir/NumSamples": skxml.IntType(),
    "RadarCollection/Area/Plane/YDir/FirstSample": skxml.IntType(),
    "RadarCollection/Area/Plane/SegmentList/Segment/StartLine": skxml.IntType(),
    "RadarCollection/Area/Plane/SegmentList/Segment/StartSample": skxml.IntType(),
    "RadarCollection/Area/Plane/SegmentList/Segment/EndLine": skxml.IntType(),
    "RadarCollection/Area/Plane/SegmentList/Segment/EndSample": skxml.IntType(),
    "RadarCollection/Area/Plane/SegmentList/Segment/Identifier": skxml.TxtType(),
    "RadarCollection/Area/Plane/Orientation": skxml.TxtType(),
    "RadarCollection/Parameter": skxml.ParameterType(),
}
TRANSCODERS |= {
    "ImageFormation/RcvChanProc/NumChanProc": skxml.IntType(),
    "ImageFormation/RcvChanProc/PRFScaleFactor": skxml.DblType(),
    "ImageFormation/RcvChanProc/ChanIndex": skxml.IntType(),
    "ImageFormation/TxRcvPolarizationProc": skxml.TxtType(),
    "ImageFormation/TStartProc": skxml.DblType(),
    "ImageFormation/TEndProc": skxml.DblType(),
    "ImageFormation/TxFrequencyProc/MinProc": skxml.DblType(),
    "ImageFormation/TxFrequencyProc/MaxProc": skxml.DblType(),
    "ImageFormation/SegmentIdentifier": skxml.TxtType(),
    "ImageFormation/ImageFormAlgo": skxml.TxtType(),
    "ImageFormation/STBeamComp": skxml.TxtType(),
    "ImageFormation/ImageBeamComp": skxml.TxtType(),
    "ImageFormation/AzAutofocus": skxml.TxtType(),
    "ImageFormation/RgAutofocus": skxml.TxtType(),
    "ImageFormation/Processing/Type": skxml.TxtType(),
    "ImageFormation/Processing/Applied": skxml.BoolType(),
    "ImageFormation/Processing/Parameter": skxml.ParameterType(),
    "ImageFormation/PolarizationCalibration/DistortCorrectionApplied": skxml.BoolType(),
    "ImageFormation/PolarizationCalibration/Distortion/CalibrationDate": skxml.XdtType(),
    "ImageFormation/PolarizationCalibration/Distortion/A": skxml.DblType(),
    "ImageFormation/PolarizationCalibration/Distortion/F1": skxml.CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/Q1": skxml.CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/Q2": skxml.CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/F2": skxml.CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/Q3": skxml.CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/Q4": skxml.CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/GainErrorA": skxml.DblType(),
    "ImageFormation/PolarizationCalibration/Distortion/GainErrorF1": skxml.DblType(),
    "ImageFormation/PolarizationCalibration/Distortion/GainErrorF2": skxml.DblType(),
    "ImageFormation/PolarizationCalibration/Distortion/PhaseErrorF1": skxml.DblType(),
    "ImageFormation/PolarizationCalibration/Distortion/PhaseErrorF2": skxml.DblType(),
}
TRANSCODERS |= {
    "SCPCOA/SCPTime": skxml.DblType(),
    "SCPCOA/ARPPos": skxml.XyzType(),
    "SCPCOA/ARPVel": skxml.XyzType(),
    "SCPCOA/ARPAcc": skxml.XyzType(),
    "SCPCOA/SideOfTrack": skxml.TxtType(),
    "SCPCOA/SlantRange": skxml.DblType(),
    "SCPCOA/GroundRange": skxml.DblType(),
    "SCPCOA/DopplerConeAng": skxml.DblType(),
    "SCPCOA/GrazeAng": skxml.DblType(),
    "SCPCOA/IncidenceAng": skxml.DblType(),
    "SCPCOA/TwistAng": skxml.DblType(),
    "SCPCOA/SlopeAng": skxml.DblType(),
    "SCPCOA/AzimAng": skxml.DblType(),
    "SCPCOA/LayoverAng": skxml.DblType(),
    "SCPCOA/Bistatic/BistaticAng": skxml.DblType(),
    "SCPCOA/Bistatic/BistaticAngRate": skxml.DblType(),
}
for d in ("Tx", "Rcv"):
    TRANSCODERS |= {
        f"SCPCOA/Bistatic/{d}Platform/Time": skxml.DblType(),
        f"SCPCOA/Bistatic/{d}Platform/Pos": skxml.XyzType(),
        f"SCPCOA/Bistatic/{d}Platform/Vel": skxml.XyzType(),
        f"SCPCOA/Bistatic/{d}Platform/Acc": skxml.XyzType(),
        f"SCPCOA/Bistatic/{d}Platform/SideOfTrack": skxml.TxtType(),
        f"SCPCOA/Bistatic/{d}Platform/SlantRange": skxml.DblType(),
        f"SCPCOA/Bistatic/{d}Platform/GroundRange": skxml.DblType(),
        f"SCPCOA/Bistatic/{d}Platform/DopplerConeAng": skxml.DblType(),
        f"SCPCOA/Bistatic/{d}Platform/GrazeAng": skxml.DblType(),
        f"SCPCOA/Bistatic/{d}Platform/IncidenceAng": skxml.DblType(),
        f"SCPCOA/Bistatic/{d}Platform/AzimAng": skxml.DblType(),
    }
TRANSCODERS |= {
    "Radiometric/NoiseLevel/NoiseLevelType": skxml.TxtType(),
    "Radiometric/NoiseLevel/NoisePoly": skxml.Poly2dType(),
    "Radiometric/RCSSFPoly": skxml.Poly2dType(),
    "Radiometric/SigmaZeroSFPoly": skxml.Poly2dType(),
    "Radiometric/BetaZeroSFPoly": skxml.Poly2dType(),
    "Radiometric/GammaZeroSFPoly": skxml.Poly2dType(),
}
for a in ("Tx", "Rcv", "TwoWay"):
    TRANSCODERS |= {
        f"Antenna/{a}/XAxisPoly": skxml.XyzPolyType(),
        f"Antenna/{a}/YAxisPoly": skxml.XyzPolyType(),
        f"Antenna/{a}/FreqZero": skxml.DblType(),
        f"Antenna/{a}/EB/DCXPoly": skxml.PolyType(),
        f"Antenna/{a}/EB/DCYPoly": skxml.PolyType(),
        f"Antenna/{a}/Array/GainPoly": skxml.Poly2dType(),
        f"Antenna/{a}/Array/PhasePoly": skxml.Poly2dType(),
        f"Antenna/{a}/Elem/GainPoly": skxml.Poly2dType(),
        f"Antenna/{a}/Elem/PhasePoly": skxml.Poly2dType(),
        f"Antenna/{a}/GainBSPoly": skxml.PolyType(),
        f"Antenna/{a}/EBFreqShift": skxml.BoolType(),
        f"Antenna/{a}/MLFreqDilation": skxml.BoolType(),
    }


def _decorr_type(xml_path):
    return {f"{xml_path}/{x}": skxml.DblType() for x in ("CorrCoefZero", "DecorrRate")}


TRANSCODERS |= {
    "ErrorStatistics/CompositeSCP/Rg": skxml.DblType(),
    "ErrorStatistics/CompositeSCP/Az": skxml.DblType(),
    "ErrorStatistics/CompositeSCP/RgAz": skxml.DblType(),
    "ErrorStatistics/BistaticCompositeSCP/RAvg": skxml.DblType(),
    "ErrorStatistics/BistaticCompositeSCP/RdotAvg": skxml.DblType(),
    "ErrorStatistics/BistaticCompositeSCP/RAvgRdotAvg": skxml.DblType(),
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
    **_decorr_type("ErrorStatistics/Components/PosVelErr/PositionDecorr"),
    "ErrorStatistics/Components/RadarSensor/RangeBias": skxml.DblType(),
    "ErrorStatistics/Components/RadarSensor/ClockFreqSF": skxml.DblType(),
    "ErrorStatistics/Components/RadarSensor/TransmitFreqSF": skxml.DblType(),
    **_decorr_type("ErrorStatistics/Components/RadarSensor/RangeBiasDecorr"),
    "ErrorStatistics/Components/TropoError/TropoRangeVertical": skxml.DblType(),
    "ErrorStatistics/Components/TropoError/TropoRangeSlant": skxml.DblType(),
    **_decorr_type("ErrorStatistics/Components/TropoError/TropoRangeDecorr"),
    "ErrorStatistics/Components/IonoError/IonoRangeVertical": skxml.DblType(),
    "ErrorStatistics/Components/IonoError/IonoRangeRateVertical": skxml.DblType(),
    "ErrorStatistics/Components/IonoError/IonoRgRgRateCC": skxml.DblType(),
    **_decorr_type("ErrorStatistics/Components/IonoError/IonoRangeVertDecorr"),
    "ErrorStatistics/BistaticComponents/PosVelErr/TxFrame": skxml.TxtType(),
    "ErrorStatistics/BistaticComponents/PosVelErr/TxPVCov": MtxType((6, 6)),
    "ErrorStatistics/BistaticComponents/PosVelErr/RcvFrame": skxml.TxtType(),
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
    "ErrorStatistics/BistaticComponents/AtmosphericError/TxSCP": skxml.DblType(),
    "ErrorStatistics/BistaticComponents/AtmosphericError/RcvSCP": skxml.DblType(),
    "ErrorStatistics/BistaticComponents/AtmosphericError/TxRcvCC": skxml.DblType(),
    "ErrorStatistics/Unmodeled/Xrow": skxml.DblType(),
    "ErrorStatistics/Unmodeled/Ycol": skxml.DblType(),
    "ErrorStatistics/Unmodeled/XrowYcol": skxml.DblType(),
    **_decorr_type("ErrorStatistics/Unmodeled/UnmodeledDecorr/Xrow"),
    **_decorr_type("ErrorStatistics/Unmodeled/UnmodeledDecorr/Ycol"),
    "ErrorStatistics/AdditionalParms/Parameter": skxml.ParameterType(),
    "ErrorStatistics/AdjustableParameterOffsets/ARPPosSCPCOA": skxml.XyzType(),
    "ErrorStatistics/AdjustableParameterOffsets/ARPVel": skxml.XyzType(),
    "ErrorStatistics/AdjustableParameterOffsets/TxTimeSCPCOA": skxml.DblType(),
    "ErrorStatistics/AdjustableParameterOffsets/RcvTimeSCPCOA": skxml.DblType(),
    "ErrorStatistics/AdjustableParameterOffsets/APOError": MtxType((8, 8)),
    "ErrorStatistics/AdjustableParameterOffsets/CompositeSCP/Rg": skxml.DblType(),
    "ErrorStatistics/AdjustableParameterOffsets/CompositeSCP/Az": skxml.DblType(),
    "ErrorStatistics/AdjustableParameterOffsets/CompositeSCP/RgAz": skxml.DblType(),
}
for p in ("Tx", "Rcv"):
    TRANSCODERS |= {
        f"ErrorStatistics/BistaticAdjustableParameterOffsets/{p}Platform/APCPosSCPCOA": skxml.XyzType(),
        f"ErrorStatistics/BistaticAdjustableParameterOffsets/{p}Platform/APCVel": skxml.XyzType(),
        f"ErrorStatistics/BistaticAdjustableParameterOffsets/{p}Platform/TimeSCPCOA": skxml.DblType(),
        f"ErrorStatistics/BistaticAdjustableParameterOffsets/{p}Platform/ClockFreqSF": skxml.DblType(),
    }
TRANSCODERS |= {
    "ErrorStatistics/BistaticAdjustableParameterOffsets/APOError": MtxType((16, 16)),
    "ErrorStatistics/BistaticAdjustableParameterOffsets/BistaticCompositeSCP/RAvg": skxml.DblType(),
    "ErrorStatistics/BistaticAdjustableParameterOffsets/BistaticCompositeSCP/RdotAvg": skxml.DblType(),
    "ErrorStatistics/BistaticAdjustableParameterOffsets/BistaticCompositeSCP/RAvgRdotAvg": skxml.DblType(),
}
TRANSCODERS |= {
    "MatchInfo/NumMatchTypes": skxml.IntType(),
    "MatchInfo/MatchType/TypeID": skxml.TxtType(),
    "MatchInfo/MatchType/CurrentIndex": skxml.IntType(),
    "MatchInfo/MatchType/NumMatchCollections": skxml.IntType(),
    "MatchInfo/MatchType/MatchCollection/CoreName": skxml.TxtType(),
    "MatchInfo/MatchType/MatchCollection/MatchIndex": skxml.IntType(),
    "MatchInfo/MatchType/MatchCollection/Parameter": skxml.ParameterType(),
}
TRANSCODERS |= {
    "RgAzComp/AzSF": skxml.DblType(),
    "RgAzComp/KazPoly": skxml.PolyType(),
}
TRANSCODERS |= {
    "PFA/FPN": skxml.XyzType(),
    "PFA/IPN": skxml.XyzType(),
    "PFA/PolarAngRefTime": skxml.DblType(),
    "PFA/PolarAngPoly": skxml.PolyType(),
    "PFA/SpatialFreqSFPoly": skxml.PolyType(),
    "PFA/Krg1": skxml.DblType(),
    "PFA/Krg2": skxml.DblType(),
    "PFA/Kaz1": skxml.DblType(),
    "PFA/Kaz2": skxml.DblType(),
    "PFA/STDeskew/Applied": skxml.BoolType(),
    "PFA/STDeskew/STDSPhasePoly": skxml.Poly2dType(),
}
TRANSCODERS |= {
    "RMA/RMAlgoType": skxml.TxtType(),
    "RMA/ImageType": skxml.TxtType(),
    "RMA/RMAT/PosRef": skxml.XyzType(),
    "RMA/RMAT/VelRef": skxml.XyzType(),
    "RMA/RMAT/DopConeAngRef": skxml.DblType(),
    "RMA/RMCR/PosRef": skxml.XyzType(),
    "RMA/RMCR/VelRef": skxml.XyzType(),
    "RMA/RMCR/DopConeAngRef": skxml.DblType(),
    "RMA/INCA/TimeCAPoly": skxml.PolyType(),
    "RMA/INCA/R_CA_SCP": skxml.DblType(),
    "RMA/INCA/FreqZero": skxml.DblType(),
    "RMA/INCA/DRateSFPoly": skxml.Poly2dType(),
    "RMA/INCA/DopCentroidPoly": skxml.Poly2dType(),
    "RMA/INCA/DopCentroidCOA": skxml.BoolType(),
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

# Matrix subelements
TRANSCODERS.update(
    {
        f"{p}/Entry": skxml.DblType()
        for p, v in TRANSCODERS.items()
        if isinstance(v, MtxType)
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
    sicd_versions = list(sarkit.standards.sicd.io.VERSION_INFO)
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
        tx_coa = t_coa - (1 / sarkit.constants.speed_of_light) * np.linalg.norm(
            npp.polyval(t_coa, params.Xmt_Poly) - scp
        )
        tr_coa = t_coa + (1 / sarkit.constants.speed_of_light) * np.linalg.norm(
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
