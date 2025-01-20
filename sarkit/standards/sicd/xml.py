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

import sarkit.constants
import sarkit.standards.sicd.io
import sarkit.standards.sicd.projection as ss_proj
import sarkit.standards.xml as ssxml


class ImageCornersType(ssxml.ListType):
    """
    Transcoder for SICD-like GeoData/ImageCorners XML parameter types.

    """

    def __init__(self) -> None:
        super().__init__("ICP", ssxml.LatLonType())

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


class MtxType(ssxml.Type):
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


TRANSCODERS: dict[str, ssxml.Type] = {
    "CollectionInfo/CollectorName": ssxml.TxtType(),
    "CollectionInfo/IlluminatorName": ssxml.TxtType(),
    "CollectionInfo/CoreName": ssxml.TxtType(),
    "CollectionInfo/CollectType": ssxml.TxtType(),
    "CollectionInfo/RadarMode/ModeType": ssxml.TxtType(),
    "CollectionInfo/RadarMode/ModeID": ssxml.TxtType(),
    "CollectionInfo/Classification": ssxml.TxtType(),
    "CollectionInfo/InformationSecurityMarking": ssxml.TxtType(),
    "CollectionInfo/CountryCode": ssxml.TxtType(),
    "CollectionInfo/Parameter": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "ImageCreation/Application": ssxml.TxtType(),
    "ImageCreation/DateTime": ssxml.XdtType(),
    "ImageCreation/Site": ssxml.TxtType(),
    "ImageCreation/Profile": ssxml.TxtType(),
}
TRANSCODERS |= {
    "ImageData/PixelType": ssxml.TxtType(),
    "ImageData/AmpTable": ssxml.ListType("Amplitude", ssxml.DblType(), index_start=0),
    "ImageData/NumRows": ssxml.IntType(),
    "ImageData/NumCols": ssxml.IntType(),
    "ImageData/FirstRow": ssxml.IntType(),
    "ImageData/FirstCol": ssxml.IntType(),
    "ImageData/FullImage/NumRows": ssxml.IntType(),
    "ImageData/FullImage/NumCols": ssxml.IntType(),
    "ImageData/SCPPixel": ssxml.RowColType(),
    "ImageData/ValidData": ssxml.ListType("Vertex", ssxml.RowColType()),
}
TRANSCODERS |= {
    "GeoData/EarthModel": ssxml.TxtType(),
    "GeoData/SCP/ECF": ssxml.XyzType(),
    "GeoData/SCP/LLH": ssxml.LatLonHaeType(),
    "GeoData/ImageCorners": ImageCornersType(),
    "GeoData/ValidData": ssxml.ListType("Vertex", ssxml.LatLonType()),
    "GeoData/GeoInfo/Desc": ssxml.ParameterType(),
    "GeoData/GeoInfo/Point": ssxml.LatLonType(),
    "GeoData/GeoInfo/Line": ssxml.ListType("Endpoint", ssxml.LatLonType()),
    "GeoData/GeoInfo/Polygon": ssxml.ListType("Vertex", ssxml.LatLonType()),
}
TRANSCODERS |= {
    "Grid/ImagePlane": ssxml.TxtType(),
    "Grid/Type": ssxml.TxtType(),
    "Grid/TimeCOAPoly": ssxml.PolyType(2),
}
for d in ("Row", "Col"):
    TRANSCODERS |= {
        f"Grid/{d}/UVectECF": ssxml.XyzType(),
        f"Grid/{d}/SS": ssxml.DblType(),
        f"Grid/{d}/ImpRespWid": ssxml.DblType(),
        f"Grid/{d}/Sgn": ssxml.IntType(),
        f"Grid/{d}/ImpRespBW": ssxml.DblType(),
        f"Grid/{d}/KCtr": ssxml.DblType(),
        f"Grid/{d}/DeltaK1": ssxml.DblType(),
        f"Grid/{d}/DeltaK2": ssxml.DblType(),
        f"Grid/{d}/DeltaKCOAPoly": ssxml.PolyType(2),
        f"Grid/{d}/WgtType/WindowName": ssxml.TxtType(),
        f"Grid/{d}/WgtType/Parameter": ssxml.ParameterType(),
        f"Grid/{d}/WgtFunct": ssxml.ListType("Wgt", ssxml.DblType()),
    }
TRANSCODERS |= {
    "Timeline/CollectStart": ssxml.XdtType(),
    "Timeline/CollectDuration": ssxml.DblType(),
    "Timeline/IPP/Set/TStart": ssxml.DblType(),
    "Timeline/IPP/Set/TEnd": ssxml.DblType(),
    "Timeline/IPP/Set/IPPStart": ssxml.IntType(),
    "Timeline/IPP/Set/IPPEnd": ssxml.IntType(),
    "Timeline/IPP/Set/IPPPoly": ssxml.PolyType(),
}
TRANSCODERS |= {
    "Position/ARPPoly": ssxml.XyzPolyType(),
    "Position/GRPPoly": ssxml.XyzPolyType(),
    "Position/TxAPCPoly": ssxml.XyzPolyType(),
    "Position/RcvAPC/RcvAPCPoly": ssxml.XyzPolyType(),
}
TRANSCODERS |= {
    "RadarCollection/TxFrequency/Min": ssxml.DblType(),
    "RadarCollection/TxFrequency/Max": ssxml.DblType(),
    "RadarCollection/RefFreqIndex": ssxml.IntType(),
    "RadarCollection/Waveform/WFParameters/TxPulseLength": ssxml.DblType(),
    "RadarCollection/Waveform/WFParameters/TxRFBandwidth": ssxml.DblType(),
    "RadarCollection/Waveform/WFParameters/TxFreqStart": ssxml.DblType(),
    "RadarCollection/Waveform/WFParameters/TxFMRate": ssxml.DblType(),
    "RadarCollection/Waveform/WFParameters/RcvDemodType": ssxml.TxtType(),
    "RadarCollection/Waveform/WFParameters/RcvWindowLength": ssxml.DblType(),
    "RadarCollection/Waveform/WFParameters/ADCSampleRate": ssxml.DblType(),
    "RadarCollection/Waveform/WFParameters/RcvIFBandwidth": ssxml.DblType(),
    "RadarCollection/Waveform/WFParameters/RcvFreqStart": ssxml.DblType(),
    "RadarCollection/Waveform/WFParameters/RcvFMRate": ssxml.DblType(),
    "RadarCollection/TxPolarization": ssxml.TxtType(),
    "RadarCollection/TxSequence/TxStep/WFIndex": ssxml.IntType(),
    "RadarCollection/TxSequence/TxStep/TxPolarization": ssxml.TxtType(),
    "RadarCollection/RcvChannels/ChanParameters/TxRcvPolarization": ssxml.TxtType(),
    "RadarCollection/RcvChannels/ChanParameters/RcvAPCIndex": ssxml.IntType(),
    "RadarCollection/Area/Corner": ssxml.ListType(
        "ACP", ssxml.LatLonHaeType(), include_size_attr=False
    ),
    "RadarCollection/Area/Plane/RefPt/ECF": ssxml.XyzType(),
    "RadarCollection/Area/Plane/RefPt/Line": ssxml.DblType(),
    "RadarCollection/Area/Plane/RefPt/Sample": ssxml.DblType(),
    "RadarCollection/Area/Plane/XDir/UVectECF": ssxml.XyzType(),
    "RadarCollection/Area/Plane/XDir/LineSpacing": ssxml.DblType(),
    "RadarCollection/Area/Plane/XDir/NumLines": ssxml.IntType(),
    "RadarCollection/Area/Plane/XDir/FirstLine": ssxml.IntType(),
    "RadarCollection/Area/Plane/YDir/UVectECF": ssxml.XyzType(),
    "RadarCollection/Area/Plane/YDir/SampleSpacing": ssxml.DblType(),
    "RadarCollection/Area/Plane/YDir/NumSamples": ssxml.IntType(),
    "RadarCollection/Area/Plane/YDir/FirstSample": ssxml.IntType(),
    "RadarCollection/Area/Plane/SegmentList/Segment/StartLine": ssxml.IntType(),
    "RadarCollection/Area/Plane/SegmentList/Segment/StartSample": ssxml.IntType(),
    "RadarCollection/Area/Plane/SegmentList/Segment/EndLine": ssxml.IntType(),
    "RadarCollection/Area/Plane/SegmentList/Segment/EndSample": ssxml.IntType(),
    "RadarCollection/Area/Plane/SegmentList/Segment/Identifier": ssxml.TxtType(),
    "RadarCollection/Area/Plane/Orientation": ssxml.TxtType(),
    "RadarCollection/Parameter": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "ImageFormation/RcvChanProc/NumChanProc": ssxml.IntType(),
    "ImageFormation/RcvChanProc/PRFScaleFactor": ssxml.DblType(),
    "ImageFormation/RcvChanProc/ChanIndex": ssxml.IntType(),
    "ImageFormation/TxRcvPolarizationProc": ssxml.TxtType(),
    "ImageFormation/TStartProc": ssxml.DblType(),
    "ImageFormation/TEndProc": ssxml.DblType(),
    "ImageFormation/TxFrequencyProc/MinProc": ssxml.DblType(),
    "ImageFormation/TxFrequencyProc/MaxProc": ssxml.DblType(),
    "ImageFormation/SegmentIdentifier": ssxml.TxtType(),
    "ImageFormation/ImageFormAlgo": ssxml.TxtType(),
    "ImageFormation/STBeamComp": ssxml.TxtType(),
    "ImageFormation/ImageBeamComp": ssxml.TxtType(),
    "ImageFormation/AzAutofocus": ssxml.TxtType(),
    "ImageFormation/RgAutofocus": ssxml.TxtType(),
    "ImageFormation/Processing/Type": ssxml.TxtType(),
    "ImageFormation/Processing/Applied": ssxml.BoolType(),
    "ImageFormation/Processing/Parameter": ssxml.ParameterType(),
    "ImageFormation/PolarizationCalibration/DistortCorrectionApplied": ssxml.BoolType(),
    "ImageFormation/PolarizationCalibration/Distortion/CalibrationDate": ssxml.XdtType(),
    "ImageFormation/PolarizationCalibration/Distortion/A": ssxml.DblType(),
    "ImageFormation/PolarizationCalibration/Distortion/F1": ssxml.CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/Q1": ssxml.CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/Q2": ssxml.CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/F2": ssxml.CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/Q3": ssxml.CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/Q4": ssxml.CmplxType(),
    "ImageFormation/PolarizationCalibration/Distortion/GainErrorA": ssxml.DblType(),
    "ImageFormation/PolarizationCalibration/Distortion/GainErrorF1": ssxml.DblType(),
    "ImageFormation/PolarizationCalibration/Distortion/GainErrorF2": ssxml.DblType(),
    "ImageFormation/PolarizationCalibration/Distortion/PhaseErrorF1": ssxml.DblType(),
    "ImageFormation/PolarizationCalibration/Distortion/PhaseErrorF2": ssxml.DblType(),
}
TRANSCODERS |= {
    "SCPCOA/SCPTime": ssxml.DblType(),
    "SCPCOA/ARPPos": ssxml.XyzType(),
    "SCPCOA/ARPVel": ssxml.XyzType(),
    "SCPCOA/ARPAcc": ssxml.XyzType(),
    "SCPCOA/SideOfTrack": ssxml.TxtType(),
    "SCPCOA/SlantRange": ssxml.DblType(),
    "SCPCOA/GroundRange": ssxml.DblType(),
    "SCPCOA/DopplerConeAng": ssxml.DblType(),
    "SCPCOA/GrazeAng": ssxml.DblType(),
    "SCPCOA/IncidenceAng": ssxml.DblType(),
    "SCPCOA/TwistAng": ssxml.DblType(),
    "SCPCOA/SlopeAng": ssxml.DblType(),
    "SCPCOA/AzimAng": ssxml.DblType(),
    "SCPCOA/LayoverAng": ssxml.DblType(),
    "SCPCOA/Bistatic/BistaticAng": ssxml.DblType(),
    "SCPCOA/Bistatic/BistaticAngRate": ssxml.DblType(),
}
for d in ("Tx", "Rcv"):
    TRANSCODERS |= {
        f"SCPCOA/Bistatic/{d}Platform/Time": ssxml.DblType(),
        f"SCPCOA/Bistatic/{d}Platform/Pos": ssxml.XyzType(),
        f"SCPCOA/Bistatic/{d}Platform/Vel": ssxml.XyzType(),
        f"SCPCOA/Bistatic/{d}Platform/Acc": ssxml.XyzType(),
        f"SCPCOA/Bistatic/{d}Platform/SideOfTrack": ssxml.TxtType(),
        f"SCPCOA/Bistatic/{d}Platform/SlantRange": ssxml.DblType(),
        f"SCPCOA/Bistatic/{d}Platform/GroundRange": ssxml.DblType(),
        f"SCPCOA/Bistatic/{d}Platform/DopplerConeAng": ssxml.DblType(),
        f"SCPCOA/Bistatic/{d}Platform/GrazeAng": ssxml.DblType(),
        f"SCPCOA/Bistatic/{d}Platform/IncidenceAng": ssxml.DblType(),
        f"SCPCOA/Bistatic/{d}Platform/AzimAng": ssxml.DblType(),
    }
TRANSCODERS |= {
    "Radiometric/NoiseLevel/NoiseLevelType": ssxml.TxtType(),
    "Radiometric/NoiseLevel/NoisePoly": ssxml.PolyType(2),
    "Radiometric/RCSSFPoly": ssxml.PolyType(2),
    "Radiometric/SigmaZeroSFPoly": ssxml.PolyType(2),
    "Radiometric/BetaZeroSFPoly": ssxml.PolyType(2),
    "Radiometric/GammaZeroSFPoly": ssxml.PolyType(2),
}
for a in ("Tx", "Rcv", "TwoWay"):
    TRANSCODERS |= {
        f"Antenna/{a}/XAxisPoly": ssxml.XyzPolyType(),
        f"Antenna/{a}/YAxisPoly": ssxml.XyzPolyType(),
        f"Antenna/{a}/FreqZero": ssxml.DblType(),
        f"Antenna/{a}/EB/DCXPoly": ssxml.PolyType(),
        f"Antenna/{a}/EB/DCYPoly": ssxml.PolyType(),
        f"Antenna/{a}/Array/GainPoly": ssxml.PolyType(2),
        f"Antenna/{a}/Array/PhasePoly": ssxml.PolyType(2),
        f"Antenna/{a}/Elem/GainPoly": ssxml.PolyType(2),
        f"Antenna/{a}/Elem/PhasePoly": ssxml.PolyType(2),
        f"Antenna/{a}/GainBSPoly": ssxml.PolyType(),
        f"Antenna/{a}/EBFreqShift": ssxml.BoolType(),
        f"Antenna/{a}/MLFreqDilation": ssxml.BoolType(),
    }


def _decorr_type(xml_path):
    return {f"{xml_path}/{x}": ssxml.DblType() for x in ("CorrCoefZero", "DecorrRate")}


TRANSCODERS |= {
    "ErrorStatistics/CompositeSCP/Rg": ssxml.DblType(),
    "ErrorStatistics/CompositeSCP/Az": ssxml.DblType(),
    "ErrorStatistics/CompositeSCP/RgAz": ssxml.DblType(),
    "ErrorStatistics/BistaticCompositeSCP/RAvg": ssxml.DblType(),
    "ErrorStatistics/BistaticCompositeSCP/RdotAvg": ssxml.DblType(),
    "ErrorStatistics/BistaticCompositeSCP/RAvgRdotAvg": ssxml.DblType(),
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
    **_decorr_type("ErrorStatistics/Components/PosVelErr/PositionDecorr"),
    "ErrorStatistics/Components/RadarSensor/RangeBias": ssxml.DblType(),
    "ErrorStatistics/Components/RadarSensor/ClockFreqSF": ssxml.DblType(),
    "ErrorStatistics/Components/RadarSensor/TransmitFreqSF": ssxml.DblType(),
    **_decorr_type("ErrorStatistics/Components/RadarSensor/RangeBiasDecorr"),
    "ErrorStatistics/Components/TropoError/TropoRangeVertical": ssxml.DblType(),
    "ErrorStatistics/Components/TropoError/TropoRangeSlant": ssxml.DblType(),
    **_decorr_type("ErrorStatistics/Components/TropoError/TropoRangeDecorr"),
    "ErrorStatistics/Components/IonoError/IonoRangeVertical": ssxml.DblType(),
    "ErrorStatistics/Components/IonoError/IonoRangeRateVertical": ssxml.DblType(),
    "ErrorStatistics/Components/IonoError/IonoRgRgRateCC": ssxml.DblType(),
    **_decorr_type("ErrorStatistics/Components/IonoError/IonoRangeVertDecorr"),
    "ErrorStatistics/BistaticComponents/PosVelErr/TxFrame": ssxml.TxtType(),
    "ErrorStatistics/BistaticComponents/PosVelErr/TxPVCov": MtxType((6, 6)),
    "ErrorStatistics/BistaticComponents/PosVelErr/RcvFrame": ssxml.TxtType(),
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
    "ErrorStatistics/BistaticComponents/AtmosphericError/TxSCP": ssxml.DblType(),
    "ErrorStatistics/BistaticComponents/AtmosphericError/RcvSCP": ssxml.DblType(),
    "ErrorStatistics/BistaticComponents/AtmosphericError/TxRcvCC": ssxml.DblType(),
    "ErrorStatistics/Unmodeled/Xrow": ssxml.DblType(),
    "ErrorStatistics/Unmodeled/Ycol": ssxml.DblType(),
    "ErrorStatistics/Unmodeled/XrowYcol": ssxml.DblType(),
    **_decorr_type("ErrorStatistics/Unmodeled/UnmodeledDecorr/Xrow"),
    **_decorr_type("ErrorStatistics/Unmodeled/UnmodeledDecorr/Ycol"),
    "ErrorStatistics/AdditionalParms/Parameter": ssxml.ParameterType(),
    "ErrorStatistics/AdjustableParameterOffsets/ARPPosSCPCOA": ssxml.XyzType(),
    "ErrorStatistics/AdjustableParameterOffsets/ARPVel": ssxml.XyzType(),
    "ErrorStatistics/AdjustableParameterOffsets/TxTimeSCPCOA": ssxml.DblType(),
    "ErrorStatistics/AdjustableParameterOffsets/RcvTimeSCPCOA": ssxml.DblType(),
    "ErrorStatistics/AdjustableParameterOffsets/APOError": MtxType((8, 8)),
    "ErrorStatistics/AdjustableParameterOffsets/CompositeSCP/Rg": ssxml.DblType(),
    "ErrorStatistics/AdjustableParameterOffsets/CompositeSCP/Az": ssxml.DblType(),
    "ErrorStatistics/AdjustableParameterOffsets/CompositeSCP/RgAz": ssxml.DblType(),
}
for p in ("Tx", "Rcv"):
    TRANSCODERS |= {
        f"ErrorStatistics/BistaticAdjustableParameterOffsets/{p}Platform/APCPosSCPCOA": ssxml.XyzType(),
        f"ErrorStatistics/BistaticAdjustableParameterOffsets/{p}Platform/APCVel": ssxml.XyzType(),
        f"ErrorStatistics/BistaticAdjustableParameterOffsets/{p}Platform/TimeSCPCOA": ssxml.DblType(),
        f"ErrorStatistics/BistaticAdjustableParameterOffsets/{p}Platform/ClockFreqSF": ssxml.DblType(),
    }
TRANSCODERS |= {
    "ErrorStatistics/BistaticAdjustableParameterOffsets/APOError": MtxType((16, 16)),
    "ErrorStatistics/BistaticAdjustableParameterOffsets/BistaticCompositeSCP/RAvg": ssxml.DblType(),
    "ErrorStatistics/BistaticAdjustableParameterOffsets/BistaticCompositeSCP/RdotAvg": ssxml.DblType(),
    "ErrorStatistics/BistaticAdjustableParameterOffsets/BistaticCompositeSCP/RAvgRdotAvg": ssxml.DblType(),
}
TRANSCODERS |= {
    "MatchInfo/NumMatchTypes": ssxml.IntType(),
    "MatchInfo/MatchType/TypeID": ssxml.TxtType(),
    "MatchInfo/MatchType/CurrentIndex": ssxml.IntType(),
    "MatchInfo/MatchType/NumMatchCollections": ssxml.IntType(),
    "MatchInfo/MatchType/MatchCollection/CoreName": ssxml.TxtType(),
    "MatchInfo/MatchType/MatchCollection/MatchIndex": ssxml.IntType(),
    "MatchInfo/MatchType/MatchCollection/Parameter": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "RgAzComp/AzSF": ssxml.DblType(),
    "RgAzComp/KazPoly": ssxml.PolyType(),
}
TRANSCODERS |= {
    "PFA/FPN": ssxml.XyzType(),
    "PFA/IPN": ssxml.XyzType(),
    "PFA/PolarAngRefTime": ssxml.DblType(),
    "PFA/PolarAngPoly": ssxml.PolyType(),
    "PFA/SpatialFreqSFPoly": ssxml.PolyType(),
    "PFA/Krg1": ssxml.DblType(),
    "PFA/Krg2": ssxml.DblType(),
    "PFA/Kaz1": ssxml.DblType(),
    "PFA/Kaz2": ssxml.DblType(),
    "PFA/STDeskew/Applied": ssxml.BoolType(),
    "PFA/STDeskew/STDSPhasePoly": ssxml.PolyType(2),
}
TRANSCODERS |= {
    "RMA/RMAlgoType": ssxml.TxtType(),
    "RMA/ImageType": ssxml.TxtType(),
    "RMA/RMAT/PosRef": ssxml.XyzType(),
    "RMA/RMAT/VelRef": ssxml.XyzType(),
    "RMA/RMAT/DopConeAngRef": ssxml.DblType(),
    "RMA/RMCR/PosRef": ssxml.XyzType(),
    "RMA/RMCR/VelRef": ssxml.XyzType(),
    "RMA/RMCR/DopConeAngRef": ssxml.DblType(),
    "RMA/INCA/TimeCAPoly": ssxml.PolyType(),
    "RMA/INCA/R_CA_SCP": ssxml.DblType(),
    "RMA/INCA/FreqZero": ssxml.DblType(),
    "RMA/INCA/DRateSFPoly": ssxml.PolyType(2),
    "RMA/INCA/DopCentroidPoly": ssxml.PolyType(2),
    "RMA/INCA/DopCentroidCOA": ssxml.BoolType(),
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

# Matrix subelements
TRANSCODERS.update(
    {
        f"{p}/Entry": ssxml.DblType()
        for p, v in TRANSCODERS.items()
        if isinstance(v, MtxType)
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
