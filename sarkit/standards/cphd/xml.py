"""
========
CPHD XML
========

Functions from CPHD Design & Implementation Description Document.

"""

import copy
import re
from collections.abc import Sequence

import lxml.etree

import sarkit.standards.cphd.io as cphd_io
import sarkit.standards.xml as ssxml


class ImageAreaCornerPointsType(ssxml.ListType):
    """
    Transcoder for CPHD-like SceneCoordinates/ImageAreaCornerPoints XML parameter types.

    """

    def __init__(self) -> None:
        super().__init__("IACP", ssxml.LatLonType(), include_size_attr=False)

    def set_elem(
        self, elem: lxml.etree.Element, val: Sequence[Sequence[float]]
    ) -> None:
        """Set the IACP children of ``elem`` using the ordered vertices from ``val``.

        Parameters
        ----------
        elem : lxml.etree.Element
            XML element to set
        val : (4, 2) array_like
            Array of [latitude (deg), longitude (deg)] image corners.

        """
        if len(val) != 4:
            raise ValueError(f"Must have 4 corner points (given {len(val)})")
        super().set_elem(elem, val)


class PvpType(ssxml.SequenceType):
    """
    Transcoder for CPHD.PVP XML parameter types.

    """

    def __init__(self) -> None:
        super().__init__(
            {
                "Offset": ssxml.IntType(),
                "Size": ssxml.IntType(),
                "Format": ssxml.TxtType(),
            }
        )

    def parse_elem(self, elem: lxml.etree.Element) -> dict:
        """Returns a dict containing the sequence of subelements encoded in ``elem``.

        Parameters
        ----------
        elem : lxml.etree.Element
            XML element to parse

        Returns
        -------
        elem_dict : dict
            Subelement values by name:

            * "Name" : `str` (`AddedPvpType` only)
            * "Offset" : `int`
            * "Size" : `int`
            * "dtype" : `numpy.dtype`
        """
        elem_dict = super().parse_subelements(elem)
        elem_dict["dtype"] = cphd_io.binary_format_string_to_dtype(elem_dict["Format"])
        del elem_dict["Format"]
        return elem_dict

    def set_elem(self, elem: lxml.etree.Element, val: dict) -> None:
        """Sets ``elem`` node using the sequence of subelements in the dict ``val``.

        Parameters
        ----------
        elem : lxml.etree.Element
            XML element to set
        val : dict
            Subelement values by name:

            * "Name" : `str` (`AddedPvpType` only)
            * "Offset" : `int`
            * "Size" : `int`
            * "dtype" : `numpy.dtype`
        """
        local_val = copy.deepcopy(val)
        local_val["Format"] = cphd_io.dtype_to_binary_format_string(local_val["dtype"])
        del local_val["dtype"]
        super().set_subelements(elem, local_val)


class AddedPvpType(PvpType):
    """
    Transcoder for CPHD.PVP.AddedPVP XML parameter types.

    """

    def __init__(self) -> None:
        super().__init__()
        self.subelements = {"Name": ssxml.TxtType(), **self.subelements}


TRANSCODERS: dict[str, ssxml.Type] = {
    "CollectionID/CollectorName": ssxml.TxtType(),
    "CollectionID/IlluminatorName": ssxml.TxtType(),
    "CollectionID/CoreName": ssxml.TxtType(),
    "CollectionID/CollectType": ssxml.TxtType(),
    "CollectionID/RadarMode/ModeType": ssxml.TxtType(),
    "CollectionID/RadarMode/ModeID": ssxml.TxtType(),
    "CollectionID/Classification": ssxml.TxtType(),
    "CollectionID/ReleaseInfo": ssxml.TxtType(),
    "CollectionID/CountryCode": ssxml.TxtType(),
    "CollectionID/Parameter": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "Global/DomainType": ssxml.TxtType(),
    "Global/SGN": ssxml.IntType(),
    "Global/Timeline/CollectionStart": ssxml.XdtType(),
    "Global/Timeline/RcvCollectionStart": ssxml.XdtType(),
    "Global/Timeline/TxTime1": ssxml.DblType(),
    "Global/Timeline/TxTime2": ssxml.DblType(),
    "Global/FxBand/FxMin": ssxml.DblType(),
    "Global/FxBand/FxMax": ssxml.DblType(),
    "Global/TOASwath/TOAMin": ssxml.DblType(),
    "Global/TOASwath/TOAMax": ssxml.DblType(),
    "Global/TropoParameters/N0": ssxml.DblType(),
    "Global/TropoParameters/RefHeight": ssxml.TxtType(),
    "Global/IonoParameters/TECV": ssxml.DblType(),
    "Global/IonoParameters/F2Height": ssxml.DblType(),
}
TRANSCODERS |= {
    "SceneCoordinates/EarthModel": ssxml.TxtType(),
    "SceneCoordinates/IARP/ECF": ssxml.XyzType(),
    "SceneCoordinates/IARP/LLH": ssxml.LatLonHaeType(),
    "SceneCoordinates/ReferenceSurface/Planar/uIAX": ssxml.XyzType(),
    "SceneCoordinates/ReferenceSurface/Planar/uIAY": ssxml.XyzType(),
    "SceneCoordinates/ReferenceSurface/HAE/uIAXLL": ssxml.LatLonType(),
    "SceneCoordinates/ReferenceSurface/HAE/uIAYLL": ssxml.LatLonType(),
    "SceneCoordinates/ImageArea/X1Y1": ssxml.XyType(),
    "SceneCoordinates/ImageArea/X2Y2": ssxml.XyType(),
    "SceneCoordinates/ImageArea/Polygon": ssxml.ListType("Vertex", ssxml.XyType()),
    "SceneCoordinates/ImageAreaCornerPoints": ImageAreaCornerPointsType(),
    "SceneCoordinates/ExtendedArea/X1Y1": ssxml.XyType(),
    "SceneCoordinates/ExtendedArea/X2Y2": ssxml.XyType(),
    "SceneCoordinates/ExtendedArea/Polygon": ssxml.ListType("Vertex", ssxml.XyType()),
    "SceneCoordinates/ImageGrid/Identifier": ssxml.TxtType(),
    "SceneCoordinates/ImageGrid/IARPLocation": ssxml.LineSampType(),
    "SceneCoordinates/ImageGrid/IAXExtent/LineSpacing": ssxml.DblType(),
    "SceneCoordinates/ImageGrid/IAXExtent/FirstLine": ssxml.IntType(),
    "SceneCoordinates/ImageGrid/IAXExtent/NumLines": ssxml.IntType(),
    "SceneCoordinates/ImageGrid/IAYExtent/SampleSpacing": ssxml.DblType(),
    "SceneCoordinates/ImageGrid/IAYExtent/FirstSample": ssxml.IntType(),
    "SceneCoordinates/ImageGrid/IAYExtent/NumSamples": ssxml.IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/NumSegments": ssxml.IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/Identifier": ssxml.TxtType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/StartLine": ssxml.IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/StartSample": ssxml.IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/EndLine": ssxml.IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/EndSample": ssxml.IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/SegmentPolygon": ssxml.ListType(
        "SV", ssxml.LineSampType()
    ),
}
TRANSCODERS |= {
    "Data/SignalArrayFormat": ssxml.TxtType(),
    "Data/NumBytesPVP": ssxml.IntType(),
    "Data/NumCPHDChannels": ssxml.IntType(),
    "Data/SignalCompressionID": ssxml.TxtType(),
    "Data/Channel/Identifier": ssxml.TxtType(),
    "Data/Channel/NumVectors": ssxml.IntType(),
    "Data/Channel/NumSamples": ssxml.IntType(),
    "Data/Channel/SignalArrayByteOffset": ssxml.IntType(),
    "Data/Channel/PVPArrayByteOffset": ssxml.IntType(),
    "Data/Channel/CompressedSignalSize": ssxml.IntType(),
    "Data/NumSupportArrays": ssxml.IntType(),
    "Data/SupportArray/Identifier": ssxml.TxtType(),
    "Data/SupportArray/NumRows": ssxml.IntType(),
    "Data/SupportArray/NumCols": ssxml.IntType(),
    "Data/SupportArray/BytesPerElement": ssxml.IntType(),
    "Data/SupportArray/ArrayByteOffset": ssxml.IntType(),
}
TRANSCODERS |= {
    "Channel/RefChId": ssxml.TxtType(),
    "Channel/FXFixedCPHD": ssxml.BoolType(),
    "Channel/TOAFixedCPHD": ssxml.BoolType(),
    "Channel/SRPFixedCPHD": ssxml.BoolType(),
    "Channel/Parameters/Identifier": ssxml.TxtType(),
    "Channel/Parameters/RefVectorIndex": ssxml.IntType(),
    "Channel/Parameters/FXFixed": ssxml.BoolType(),
    "Channel/Parameters/TOAFixed": ssxml.BoolType(),
    "Channel/Parameters/SRPFixed": ssxml.BoolType(),
    "Channel/Parameters/SignalNormal": ssxml.BoolType(),
    "Channel/Parameters/Polarization/TxPol": ssxml.TxtType(),
    "Channel/Parameters/Polarization/RcvPol": ssxml.TxtType(),
    "Channel/Parameters/Polarization/TxPolRef/AmpH": ssxml.DblType(),
    "Channel/Parameters/Polarization/TxPolRef/AmpV": ssxml.DblType(),
    "Channel/Parameters/Polarization/TxPolRef/PhaseV": ssxml.DblType(),
    "Channel/Parameters/Polarization/RcvPolRef/AmpH": ssxml.DblType(),
    "Channel/Parameters/Polarization/RcvPolRef/AmpV": ssxml.DblType(),
    "Channel/Parameters/Polarization/RcvPolRef/PhaseV": ssxml.DblType(),
    "Channel/Parameters/FxC": ssxml.DblType(),
    "Channel/Parameters/FxBW": ssxml.DblType(),
    "Channel/Parameters/FxBWNoise": ssxml.DblType(),
    "Channel/Parameters/TOASaved": ssxml.DblType(),
    "Channel/Parameters/TOAExtended/TOAExtSaved": ssxml.DblType(),
    "Channel/Parameters/TOAExtended/LFMEclipse/FxEarlyLow": ssxml.DblType(),
    "Channel/Parameters/TOAExtended/LFMEclipse/FxEarlyHigh": ssxml.DblType(),
    "Channel/Parameters/TOAExtended/LFMEclipse/FxLateLow": ssxml.DblType(),
    "Channel/Parameters/TOAExtended/LFMEclipse/FxLateHigh": ssxml.DblType(),
    "Channel/Parameters/DwellTimes/CODId": ssxml.TxtType(),
    "Channel/Parameters/DwellTimes/DwellId": ssxml.TxtType(),
    "Channel/Parameters/DwellTimes/DTAId": ssxml.TxtType(),
    "Channel/Parameters/DwellTimes/UseDTA": ssxml.BoolType(),
    "Channel/Parameters/ImageArea/X1Y1": ssxml.XyType(),
    "Channel/Parameters/ImageArea/X2Y2": ssxml.XyType(),
    "Channel/Parameters/ImageArea/Polygon": ssxml.ListType("Vertex", ssxml.XyType()),
    "Channel/Parameters/Antenna/TxAPCId": ssxml.TxtType(),
    "Channel/Parameters/Antenna/TxAPATId": ssxml.TxtType(),
    "Channel/Parameters/Antenna/RcvAPCId": ssxml.TxtType(),
    "Channel/Parameters/Antenna/RcvAPATId": ssxml.TxtType(),
    "Channel/Parameters/TxRcv/TxWFId": ssxml.TxtType(),
    "Channel/Parameters/TxRcv/RcvId": ssxml.TxtType(),
    "Channel/Parameters/TgtRefLevel/PTRef": ssxml.DblType(),
    "Channel/Parameters/NoiseLevel/PNRef": ssxml.DblType(),
    "Channel/Parameters/NoiseLevel/BNRef": ssxml.DblType(),
    "Channel/Parameters/NoiseLevel/FxNoiseProfile/Point/Fx": ssxml.DblType(),
    "Channel/Parameters/NoiseLevel/FxNoiseProfile/Point/PN": ssxml.DblType(),
    "Channel/AddedParameters/Parameter": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "PVP/TxTime": PvpType(),
    "PVP/TxPos": PvpType(),
    "PVP/TxVel": PvpType(),
    "PVP/RcvTime": PvpType(),
    "PVP/RcvPos": PvpType(),
    "PVP/RcvVel": PvpType(),
    "PVP/SRPPos": PvpType(),
    "PVP/AmpSF": PvpType(),
    "PVP/aFDOP": PvpType(),
    "PVP/aFRR1": PvpType(),
    "PVP/aFRR2": PvpType(),
    "PVP/FX1": PvpType(),
    "PVP/FX2": PvpType(),
    "PVP/FXN1": PvpType(),
    "PVP/FXN2": PvpType(),
    "PVP/TOA1": PvpType(),
    "PVP/TOA2": PvpType(),
    "PVP/TOAE1": PvpType(),
    "PVP/TOAE2": PvpType(),
    "PVP/TDTropoSRP": PvpType(),
    "PVP/TDIonoSRP": PvpType(),
    "PVP/SC0": PvpType(),
    "PVP/SCSS": PvpType(),
    "PVP/SIGNAL": PvpType(),
    "PVP/TxAntenna/TxACX": PvpType(),
    "PVP/TxAntenna/TxACY": PvpType(),
    "PVP/TxAntenna/TxEB": PvpType(),
    "PVP/RcvAntenna/RcvACX": PvpType(),
    "PVP/RcvAntenna/RcvACY": PvpType(),
    "PVP/RcvAntenna/RcvEB": PvpType(),
    "PVP/AddedPVP": AddedPvpType(),
}
TRANSCODERS |= {
    "SupportArray/IAZArray/Identifier": ssxml.TxtType(),
    "SupportArray/IAZArray/ElementFormat": ssxml.TxtType(),
    "SupportArray/IAZArray/X0": ssxml.DblType(),
    "SupportArray/IAZArray/Y0": ssxml.DblType(),
    "SupportArray/IAZArray/XSS": ssxml.DblType(),
    "SupportArray/IAZArray/YSS": ssxml.DblType(),
    "SupportArray/IAZArray/NODATA": ssxml.HexType(),
    "SupportArray/AntGainPhase/Identifier": ssxml.TxtType(),
    "SupportArray/AntGainPhase/ElementFormat": ssxml.TxtType(),
    "SupportArray/AntGainPhase/X0": ssxml.DblType(),
    "SupportArray/AntGainPhase/Y0": ssxml.DblType(),
    "SupportArray/AntGainPhase/XSS": ssxml.DblType(),
    "SupportArray/AntGainPhase/YSS": ssxml.DblType(),
    "SupportArray/AntGainPhase/NODATA": ssxml.HexType(),
    "SupportArray/DwellTimeArray/Identifier": ssxml.TxtType(),
    "SupportArray/DwellTimeArray/ElementFormat": ssxml.TxtType(),
    "SupportArray/DwellTimeArray/X0": ssxml.DblType(),
    "SupportArray/DwellTimeArray/Y0": ssxml.DblType(),
    "SupportArray/DwellTimeArray/XSS": ssxml.DblType(),
    "SupportArray/DwellTimeArray/YSS": ssxml.DblType(),
    "SupportArray/DwellTimeArray/NODATA": ssxml.HexType(),
    "SupportArray/AddedSupportArray/Identifier": ssxml.TxtType(),
    "SupportArray/AddedSupportArray/ElementFormat": ssxml.TxtType(),
    "SupportArray/AddedSupportArray/X0": ssxml.DblType(),
    "SupportArray/AddedSupportArray/Y0": ssxml.DblType(),
    "SupportArray/AddedSupportArray/XSS": ssxml.DblType(),
    "SupportArray/AddedSupportArray/YSS": ssxml.DblType(),
    "SupportArray/AddedSupportArray/NODATA": ssxml.HexType(),
    "SupportArray/AddedSupportArray/XUnits": ssxml.TxtType(),
    "SupportArray/AddedSupportArray/YUnits": ssxml.TxtType(),
    "SupportArray/AddedSupportArray/ZUnits": ssxml.TxtType(),
    "SupportArray/AddedSupportArray/Parameter": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "Dwell/NumCODTimes": ssxml.IntType(),
    "Dwell/CODTime/Identifier": ssxml.TxtType(),
    "Dwell/CODTime/CODTimePoly": ssxml.PolyType(2),
    "Dwell/NumDwellTimes": ssxml.IntType(),
    "Dwell/DwellTime/Identifier": ssxml.TxtType(),
    "Dwell/DwellTime/DwellTimePoly": ssxml.PolyType(2),
}
TRANSCODERS |= {
    "ReferenceGeometry/SRP/ECF": ssxml.XyzType(),
    "ReferenceGeometry/SRP/IAC": ssxml.XyzType(),
    "ReferenceGeometry/ReferenceTime": ssxml.DblType(),
    "ReferenceGeometry/SRPCODTime": ssxml.DblType(),
    "ReferenceGeometry/SRPDwellTime": ssxml.DblType(),
    "ReferenceGeometry/Monostatic/ARPPos": ssxml.XyzType(),
    "ReferenceGeometry/Monostatic/ARPVel": ssxml.XyzType(),
    "ReferenceGeometry/Monostatic/SideOfTrack": ssxml.TxtType(),
    "ReferenceGeometry/Monostatic/SlantRange": ssxml.DblType(),
    "ReferenceGeometry/Monostatic/GroundRange": ssxml.DblType(),
    "ReferenceGeometry/Monostatic/DopplerConeAngle": ssxml.DblType(),
    "ReferenceGeometry/Monostatic/GrazeAngle": ssxml.DblType(),
    "ReferenceGeometry/Monostatic/IncidenceAngle": ssxml.DblType(),
    "ReferenceGeometry/Monostatic/AzimuthAngle": ssxml.DblType(),
    "ReferenceGeometry/Monostatic/TwistAngle": ssxml.DblType(),
    "ReferenceGeometry/Monostatic/SlopeAngle": ssxml.DblType(),
    "ReferenceGeometry/Monostatic/LayoverAngle": ssxml.DblType(),
    "ReferenceGeometry/Bistatic/AzimuthAngle": ssxml.DblType(),
    "ReferenceGeometry/Bistatic/AzimuthAngleRate": ssxml.DblType(),
    "ReferenceGeometry/Bistatic/BistaticAngle": ssxml.DblType(),
    "ReferenceGeometry/Bistatic/BistaticAngleRate": ssxml.DblType(),
    "ReferenceGeometry/Bistatic/GrazeAngle": ssxml.DblType(),
    "ReferenceGeometry/Bistatic/TwistAngle": ssxml.DblType(),
    "ReferenceGeometry/Bistatic/SlopeAngle": ssxml.DblType(),
    "ReferenceGeometry/Bistatic/LayoverAngle": ssxml.DblType(),
}
for d in ("Tx", "Rcv"):
    TRANSCODERS |= {
        f"ReferenceGeometry/Bistatic/{d}Platform/Time": ssxml.DblType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/Pos": ssxml.XyzType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/Vel": ssxml.XyzType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/SideOfTrack": ssxml.TxtType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/SlantRange": ssxml.DblType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/GroundRange": ssxml.DblType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/DopplerConeAngle": ssxml.DblType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/GrazeAngle": ssxml.DblType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/IncidenceAngle": ssxml.DblType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/AzimuthAngle": ssxml.DblType(),
    }
TRANSCODERS |= {
    "Antenna/NumACFs": ssxml.IntType(),
    "Antenna/NumAPCs": ssxml.IntType(),
    "Antenna/NumAntPats": ssxml.IntType(),
    "Antenna/AntCoordFrame/Identifier": ssxml.TxtType(),
    "Antenna/AntCoordFrame/XAxisPoly": ssxml.XyzPolyType(),
    "Antenna/AntCoordFrame/YAxisPoly": ssxml.XyzPolyType(),
    "Antenna/AntCoordFrame/UseACFPVP": ssxml.BoolType(),
    "Antenna/AntPhaseCenter/Identifier": ssxml.TxtType(),
    "Antenna/AntPhaseCenter/ACFId": ssxml.TxtType(),
    "Antenna/AntPhaseCenter/APCXYZ": ssxml.XyzType(),
    "Antenna/AntPattern/Identifier": ssxml.TxtType(),
    "Antenna/AntPattern/FreqZero": ssxml.DblType(),
    "Antenna/AntPattern/GainZero": ssxml.DblType(),
    "Antenna/AntPattern/EBFreqShift": ssxml.BoolType(),
    "Antenna/AntPattern/EBFreqShiftSF/DCXSF": ssxml.DblType(),
    "Antenna/AntPattern/EBFreqShiftSF/DCYSF": ssxml.DblType(),
    "Antenna/AntPattern/MLFreqDilation": ssxml.BoolType(),
    "Antenna/AntPattern/MLFreqDilationSF/DCXSF": ssxml.DblType(),
    "Antenna/AntPattern/MLFreqDilationSF/DCYSF": ssxml.DblType(),
    "Antenna/AntPattern/GainBSPoly": ssxml.PolyType(),
    "Antenna/AntPattern/AntPolRef/AmpX": ssxml.DblType(),
    "Antenna/AntPattern/AntPolRef/AmpY": ssxml.DblType(),
    "Antenna/AntPattern/AntPolRef/PhaseY": ssxml.DblType(),
    "Antenna/AntPattern/EB/DCXPoly": ssxml.PolyType(),
    "Antenna/AntPattern/EB/DCYPoly": ssxml.PolyType(),
    "Antenna/AntPattern/EB/UseEBPVP": ssxml.BoolType(),
    "Antenna/AntPattern/Array/GainPoly": ssxml.PolyType(2),
    "Antenna/AntPattern/Array/PhasePoly": ssxml.PolyType(2),
    "Antenna/AntPattern/Array/AntGPId": ssxml.TxtType(),
    "Antenna/AntPattern/Element/GainPoly": ssxml.PolyType(2),
    "Antenna/AntPattern/Element/PhasePoly": ssxml.PolyType(2),
    "Antenna/AntPattern/Element/AntGPId": ssxml.TxtType(),
    "Antenna/AntPattern/GainPhaseArray/Freq": ssxml.DblType(),
    "Antenna/AntPattern/GainPhaseArray/ArrayId": ssxml.TxtType(),
    "Antenna/AntPattern/GainPhaseArray/ElementId": ssxml.TxtType(),
}
TRANSCODERS |= {
    "TxRcv/NumTxWFs": ssxml.IntType(),
    "TxRcv/TxWFParameters/Identifier": ssxml.TxtType(),
    "TxRcv/TxWFParameters/PulseLength": ssxml.DblType(),
    "TxRcv/TxWFParameters/RFBandwidth": ssxml.DblType(),
    "TxRcv/TxWFParameters/FreqCenter": ssxml.DblType(),
    "TxRcv/TxWFParameters/LFMRate": ssxml.DblType(),
    "TxRcv/TxWFParameters/Polarization": ssxml.TxtType(),
    "TxRcv/TxWFParameters/Power": ssxml.DblType(),
    "TxRcv/NumRcvs": ssxml.IntType(),
    "TxRcv/RcvParameters/Identifier": ssxml.TxtType(),
    "TxRcv/RcvParameters/WindowLength": ssxml.DblType(),
    "TxRcv/RcvParameters/SampleRate": ssxml.DblType(),
    "TxRcv/RcvParameters/IFFilterBW": ssxml.DblType(),
    "TxRcv/RcvParameters/FreqCenter": ssxml.DblType(),
    "TxRcv/RcvParameters/LFMRate": ssxml.DblType(),
    "TxRcv/RcvParameters/Polarization": ssxml.TxtType(),
    "TxRcv/RcvParameters/PathGain": ssxml.DblType(),
}


def _decorr_type(xml_path):
    return {f"{xml_path}/{x}": ssxml.DblType() for x in ("CorrCoefZero", "DecorrRate")}


TRANSCODERS |= {
    "ErrorParameters/Monostatic/PosVelErr/Frame": ssxml.TxtType(),
    "ErrorParameters/Monostatic/PosVelErr/P1": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/P2": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/P3": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/V1": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/V2": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/V3": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P1P2": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P1P3": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P1V1": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P1V2": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P1V3": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P2P3": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P2V1": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P2V2": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P2V3": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P3V1": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P3V2": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P3V3": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/V1V2": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/V1V3": ssxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/V2V3": ssxml.DblType(),
    **_decorr_type("ErrorParameters/Monostatic/PosVelErr/PositionDecorr"),
    "ErrorParameters/Monostatic/RadarSensor/RangeBias": ssxml.DblType(),
    "ErrorParameters/Monostatic/RadarSensor/ClockFreqSF": ssxml.DblType(),
    "ErrorParameters/Monostatic/RadarSensor/CollectionStartTime": ssxml.DblType(),
    **_decorr_type("ErrorParameters/Monostatic/RadarSensor/RangeBiasDecorr"),
    "ErrorParameters/Monostatic/TropoError/TropoRangeVertical": ssxml.DblType(),
    "ErrorParameters/Monostatic/TropoError/TropoRangeSlant": ssxml.DblType(),
    **_decorr_type("ErrorParameters/Monostatic/TropoError/TropoRangeDecorr"),
    "ErrorParameters/Monostatic/IonoError/IonoRangeVertical": ssxml.DblType(),
    "ErrorParameters/Monostatic/IonoError/IonoRangeRateVertical": ssxml.DblType(),
    "ErrorParameters/Monostatic/IonoError/IonoRgRgRateCC": ssxml.DblType(),
    **_decorr_type("ErrorParameters/Monostatic/IonoError/IonoRangeVertDecorr"),
    "ErrorParameters/Monostatic/AddedParameters/Parameter": ssxml.ParameterType(),
    "ErrorParameters/Bistatic/AddedParameters/Parameter": ssxml.ParameterType(),
}
for d in ("Tx", "Rcv"):
    TRANSCODERS |= {
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/Frame": ssxml.TxtType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/P1": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/P2": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/P3": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/V1": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/V2": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/V3": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P1P2": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P1P3": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P1V1": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P1V2": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P1V3": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P2P3": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P2V1": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P2V2": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P2V3": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P3V1": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P3V2": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P3V3": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/V1V2": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/V1V3": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/V2V3": ssxml.DblType(),
        **_decorr_type(
            f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/PositionDecorr"
        ),
        f"ErrorParameters/Bistatic/{d}Platform/RadarSensor/DelayBias": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/RadarSensor/ClockFreqSF": ssxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/RadarSensor/CollectionStartTime": ssxml.DblType(),
    }
TRANSCODERS |= {
    "ProductInfo/Profile": ssxml.TxtType(),
    "ProductInfo/CreationInfo/Application": ssxml.TxtType(),
    "ProductInfo/CreationInfo/DateTime": ssxml.XdtType(),
    "ProductInfo/CreationInfo/Site": ssxml.TxtType(),
    "ProductInfo/CreationInfo/Parameter": ssxml.ParameterType(),
    "ProductInfo/Parameter": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "GeoInfo/Desc": ssxml.ParameterType(),
    "GeoInfo/Point": ssxml.LatLonType(),
    "GeoInfo/Line": ssxml.ListType("Endpoint", ssxml.LatLonType()),
    "GeoInfo/Polygon": ssxml.ListType("Vertex", ssxml.LatLonType()),
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
    XmlHelper for Compensated Phase History Data (CPHD).

    """

    _transcoders_ = TRANSCODERS

    def _get_simple_path(self, elem):
        return re.sub(r"(GeoInfo/)+", "GeoInfo/", super()._get_simple_path(elem))
