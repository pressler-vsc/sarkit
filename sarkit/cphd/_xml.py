"""
Functions for interacting with CPHD XML
"""

import copy
import re
from collections.abc import Sequence

import lxml.etree

import sarkit.cphd._io as cphd_io
import sarkit.xmlhelp as skxml


class ImageAreaCornerPointsType(skxml.ListType):
    """
    Transcoder for CPHD-like SceneCoordinates/ImageAreaCornerPoints XML parameter types.

    """

    def __init__(self) -> None:
        super().__init__("IACP", skxml.LatLonType(), include_size_attr=False)

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


class PvpType(skxml.SequenceType):
    """
    Transcoder for CPHD.PVP XML parameter types.

    """

    def __init__(self) -> None:
        super().__init__(
            {
                "Offset": skxml.IntType(),
                "Size": skxml.IntType(),
                "Format": skxml.TxtType(),
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
        self.subelements = {"Name": skxml.TxtType(), **self.subelements}


TRANSCODERS: dict[str, skxml.Type] = {
    "CollectionID/CollectorName": skxml.TxtType(),
    "CollectionID/IlluminatorName": skxml.TxtType(),
    "CollectionID/CoreName": skxml.TxtType(),
    "CollectionID/CollectType": skxml.TxtType(),
    "CollectionID/RadarMode/ModeType": skxml.TxtType(),
    "CollectionID/RadarMode/ModeID": skxml.TxtType(),
    "CollectionID/Classification": skxml.TxtType(),
    "CollectionID/ReleaseInfo": skxml.TxtType(),
    "CollectionID/CountryCode": skxml.TxtType(),
    "CollectionID/Parameter": skxml.ParameterType(),
}
TRANSCODERS |= {
    "Global/DomainType": skxml.TxtType(),
    "Global/SGN": skxml.IntType(),
    "Global/Timeline/CollectionStart": skxml.XdtType(),
    "Global/Timeline/RcvCollectionStart": skxml.XdtType(),
    "Global/Timeline/TxTime1": skxml.DblType(),
    "Global/Timeline/TxTime2": skxml.DblType(),
    "Global/FxBand/FxMin": skxml.DblType(),
    "Global/FxBand/FxMax": skxml.DblType(),
    "Global/TOASwath/TOAMin": skxml.DblType(),
    "Global/TOASwath/TOAMax": skxml.DblType(),
    "Global/TropoParameters/N0": skxml.DblType(),
    "Global/TropoParameters/RefHeight": skxml.TxtType(),
    "Global/IonoParameters/TECV": skxml.DblType(),
    "Global/IonoParameters/F2Height": skxml.DblType(),
}
TRANSCODERS |= {
    "SceneCoordinates/EarthModel": skxml.TxtType(),
    "SceneCoordinates/IARP/ECF": skxml.XyzType(),
    "SceneCoordinates/IARP/LLH": skxml.LatLonHaeType(),
    "SceneCoordinates/ReferenceSurface/Planar/uIAX": skxml.XyzType(),
    "SceneCoordinates/ReferenceSurface/Planar/uIAY": skxml.XyzType(),
    "SceneCoordinates/ReferenceSurface/HAE/uIAXLL": skxml.LatLonType(),
    "SceneCoordinates/ReferenceSurface/HAE/uIAYLL": skxml.LatLonType(),
    "SceneCoordinates/ImageArea/X1Y1": skxml.XyType(),
    "SceneCoordinates/ImageArea/X2Y2": skxml.XyType(),
    "SceneCoordinates/ImageArea/Polygon": skxml.ListType("Vertex", skxml.XyType()),
    "SceneCoordinates/ImageAreaCornerPoints": ImageAreaCornerPointsType(),
    "SceneCoordinates/ExtendedArea/X1Y1": skxml.XyType(),
    "SceneCoordinates/ExtendedArea/X2Y2": skxml.XyType(),
    "SceneCoordinates/ExtendedArea/Polygon": skxml.ListType("Vertex", skxml.XyType()),
    "SceneCoordinates/ImageGrid/Identifier": skxml.TxtType(),
    "SceneCoordinates/ImageGrid/IARPLocation": skxml.LineSampType(),
    "SceneCoordinates/ImageGrid/IAXExtent/LineSpacing": skxml.DblType(),
    "SceneCoordinates/ImageGrid/IAXExtent/FirstLine": skxml.IntType(),
    "SceneCoordinates/ImageGrid/IAXExtent/NumLines": skxml.IntType(),
    "SceneCoordinates/ImageGrid/IAYExtent/SampleSpacing": skxml.DblType(),
    "SceneCoordinates/ImageGrid/IAYExtent/FirstSample": skxml.IntType(),
    "SceneCoordinates/ImageGrid/IAYExtent/NumSamples": skxml.IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/NumSegments": skxml.IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/Identifier": skxml.TxtType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/StartLine": skxml.IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/StartSample": skxml.IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/EndLine": skxml.IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/EndSample": skxml.IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/SegmentPolygon": skxml.ListType(
        "SV", skxml.LineSampType()
    ),
}
TRANSCODERS |= {
    "Data/SignalArrayFormat": skxml.TxtType(),
    "Data/NumBytesPVP": skxml.IntType(),
    "Data/NumCPHDChannels": skxml.IntType(),
    "Data/SignalCompressionID": skxml.TxtType(),
    "Data/Channel/Identifier": skxml.TxtType(),
    "Data/Channel/NumVectors": skxml.IntType(),
    "Data/Channel/NumSamples": skxml.IntType(),
    "Data/Channel/SignalArrayByteOffset": skxml.IntType(),
    "Data/Channel/PVPArrayByteOffset": skxml.IntType(),
    "Data/Channel/CompressedSignalSize": skxml.IntType(),
    "Data/NumSupportArrays": skxml.IntType(),
    "Data/SupportArray/Identifier": skxml.TxtType(),
    "Data/SupportArray/NumRows": skxml.IntType(),
    "Data/SupportArray/NumCols": skxml.IntType(),
    "Data/SupportArray/BytesPerElement": skxml.IntType(),
    "Data/SupportArray/ArrayByteOffset": skxml.IntType(),
}
TRANSCODERS |= {
    "Channel/RefChId": skxml.TxtType(),
    "Channel/FXFixedCPHD": skxml.BoolType(),
    "Channel/TOAFixedCPHD": skxml.BoolType(),
    "Channel/SRPFixedCPHD": skxml.BoolType(),
    "Channel/Parameters/Identifier": skxml.TxtType(),
    "Channel/Parameters/RefVectorIndex": skxml.IntType(),
    "Channel/Parameters/FXFixed": skxml.BoolType(),
    "Channel/Parameters/TOAFixed": skxml.BoolType(),
    "Channel/Parameters/SRPFixed": skxml.BoolType(),
    "Channel/Parameters/SignalNormal": skxml.BoolType(),
    "Channel/Parameters/Polarization/TxPol": skxml.TxtType(),
    "Channel/Parameters/Polarization/RcvPol": skxml.TxtType(),
    "Channel/Parameters/Polarization/TxPolRef/AmpH": skxml.DblType(),
    "Channel/Parameters/Polarization/TxPolRef/AmpV": skxml.DblType(),
    "Channel/Parameters/Polarization/TxPolRef/PhaseV": skxml.DblType(),
    "Channel/Parameters/Polarization/RcvPolRef/AmpH": skxml.DblType(),
    "Channel/Parameters/Polarization/RcvPolRef/AmpV": skxml.DblType(),
    "Channel/Parameters/Polarization/RcvPolRef/PhaseV": skxml.DblType(),
    "Channel/Parameters/FxC": skxml.DblType(),
    "Channel/Parameters/FxBW": skxml.DblType(),
    "Channel/Parameters/FxBWNoise": skxml.DblType(),
    "Channel/Parameters/TOASaved": skxml.DblType(),
    "Channel/Parameters/TOAExtended/TOAExtSaved": skxml.DblType(),
    "Channel/Parameters/TOAExtended/LFMEclipse/FxEarlyLow": skxml.DblType(),
    "Channel/Parameters/TOAExtended/LFMEclipse/FxEarlyHigh": skxml.DblType(),
    "Channel/Parameters/TOAExtended/LFMEclipse/FxLateLow": skxml.DblType(),
    "Channel/Parameters/TOAExtended/LFMEclipse/FxLateHigh": skxml.DblType(),
    "Channel/Parameters/DwellTimes/CODId": skxml.TxtType(),
    "Channel/Parameters/DwellTimes/DwellId": skxml.TxtType(),
    "Channel/Parameters/DwellTimes/DTAId": skxml.TxtType(),
    "Channel/Parameters/DwellTimes/UseDTA": skxml.BoolType(),
    "Channel/Parameters/ImageArea/X1Y1": skxml.XyType(),
    "Channel/Parameters/ImageArea/X2Y2": skxml.XyType(),
    "Channel/Parameters/ImageArea/Polygon": skxml.ListType("Vertex", skxml.XyType()),
    "Channel/Parameters/Antenna/TxAPCId": skxml.TxtType(),
    "Channel/Parameters/Antenna/TxAPATId": skxml.TxtType(),
    "Channel/Parameters/Antenna/RcvAPCId": skxml.TxtType(),
    "Channel/Parameters/Antenna/RcvAPATId": skxml.TxtType(),
    "Channel/Parameters/TxRcv/TxWFId": skxml.TxtType(),
    "Channel/Parameters/TxRcv/RcvId": skxml.TxtType(),
    "Channel/Parameters/TgtRefLevel/PTRef": skxml.DblType(),
    "Channel/Parameters/NoiseLevel/PNRef": skxml.DblType(),
    "Channel/Parameters/NoiseLevel/BNRef": skxml.DblType(),
    "Channel/Parameters/NoiseLevel/FxNoiseProfile/Point/Fx": skxml.DblType(),
    "Channel/Parameters/NoiseLevel/FxNoiseProfile/Point/PN": skxml.DblType(),
    "Channel/AddedParameters/Parameter": skxml.ParameterType(),
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
    "SupportArray/IAZArray/Identifier": skxml.TxtType(),
    "SupportArray/IAZArray/ElementFormat": skxml.TxtType(),
    "SupportArray/IAZArray/X0": skxml.DblType(),
    "SupportArray/IAZArray/Y0": skxml.DblType(),
    "SupportArray/IAZArray/XSS": skxml.DblType(),
    "SupportArray/IAZArray/YSS": skxml.DblType(),
    "SupportArray/IAZArray/NODATA": skxml.HexType(),
    "SupportArray/AntGainPhase/Identifier": skxml.TxtType(),
    "SupportArray/AntGainPhase/ElementFormat": skxml.TxtType(),
    "SupportArray/AntGainPhase/X0": skxml.DblType(),
    "SupportArray/AntGainPhase/Y0": skxml.DblType(),
    "SupportArray/AntGainPhase/XSS": skxml.DblType(),
    "SupportArray/AntGainPhase/YSS": skxml.DblType(),
    "SupportArray/AntGainPhase/NODATA": skxml.HexType(),
    "SupportArray/DwellTimeArray/Identifier": skxml.TxtType(),
    "SupportArray/DwellTimeArray/ElementFormat": skxml.TxtType(),
    "SupportArray/DwellTimeArray/X0": skxml.DblType(),
    "SupportArray/DwellTimeArray/Y0": skxml.DblType(),
    "SupportArray/DwellTimeArray/XSS": skxml.DblType(),
    "SupportArray/DwellTimeArray/YSS": skxml.DblType(),
    "SupportArray/DwellTimeArray/NODATA": skxml.HexType(),
    "SupportArray/AddedSupportArray/Identifier": skxml.TxtType(),
    "SupportArray/AddedSupportArray/ElementFormat": skxml.TxtType(),
    "SupportArray/AddedSupportArray/X0": skxml.DblType(),
    "SupportArray/AddedSupportArray/Y0": skxml.DblType(),
    "SupportArray/AddedSupportArray/XSS": skxml.DblType(),
    "SupportArray/AddedSupportArray/YSS": skxml.DblType(),
    "SupportArray/AddedSupportArray/NODATA": skxml.HexType(),
    "SupportArray/AddedSupportArray/XUnits": skxml.TxtType(),
    "SupportArray/AddedSupportArray/YUnits": skxml.TxtType(),
    "SupportArray/AddedSupportArray/ZUnits": skxml.TxtType(),
    "SupportArray/AddedSupportArray/Parameter": skxml.ParameterType(),
}
TRANSCODERS |= {
    "Dwell/NumCODTimes": skxml.IntType(),
    "Dwell/CODTime/Identifier": skxml.TxtType(),
    "Dwell/CODTime/CODTimePoly": skxml.Poly2dType(),
    "Dwell/NumDwellTimes": skxml.IntType(),
    "Dwell/DwellTime/Identifier": skxml.TxtType(),
    "Dwell/DwellTime/DwellTimePoly": skxml.Poly2dType(),
}
TRANSCODERS |= {
    "ReferenceGeometry/SRP/ECF": skxml.XyzType(),
    "ReferenceGeometry/SRP/IAC": skxml.XyzType(),
    "ReferenceGeometry/ReferenceTime": skxml.DblType(),
    "ReferenceGeometry/SRPCODTime": skxml.DblType(),
    "ReferenceGeometry/SRPDwellTime": skxml.DblType(),
    "ReferenceGeometry/Monostatic/ARPPos": skxml.XyzType(),
    "ReferenceGeometry/Monostatic/ARPVel": skxml.XyzType(),
    "ReferenceGeometry/Monostatic/SideOfTrack": skxml.TxtType(),
    "ReferenceGeometry/Monostatic/SlantRange": skxml.DblType(),
    "ReferenceGeometry/Monostatic/GroundRange": skxml.DblType(),
    "ReferenceGeometry/Monostatic/DopplerConeAngle": skxml.DblType(),
    "ReferenceGeometry/Monostatic/GrazeAngle": skxml.DblType(),
    "ReferenceGeometry/Monostatic/IncidenceAngle": skxml.DblType(),
    "ReferenceGeometry/Monostatic/AzimuthAngle": skxml.DblType(),
    "ReferenceGeometry/Monostatic/TwistAngle": skxml.DblType(),
    "ReferenceGeometry/Monostatic/SlopeAngle": skxml.DblType(),
    "ReferenceGeometry/Monostatic/LayoverAngle": skxml.DblType(),
    "ReferenceGeometry/Bistatic/AzimuthAngle": skxml.DblType(),
    "ReferenceGeometry/Bistatic/AzimuthAngleRate": skxml.DblType(),
    "ReferenceGeometry/Bistatic/BistaticAngle": skxml.DblType(),
    "ReferenceGeometry/Bistatic/BistaticAngleRate": skxml.DblType(),
    "ReferenceGeometry/Bistatic/GrazeAngle": skxml.DblType(),
    "ReferenceGeometry/Bistatic/TwistAngle": skxml.DblType(),
    "ReferenceGeometry/Bistatic/SlopeAngle": skxml.DblType(),
    "ReferenceGeometry/Bistatic/LayoverAngle": skxml.DblType(),
}
for d in ("Tx", "Rcv"):
    TRANSCODERS |= {
        f"ReferenceGeometry/Bistatic/{d}Platform/Time": skxml.DblType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/Pos": skxml.XyzType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/Vel": skxml.XyzType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/SideOfTrack": skxml.TxtType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/SlantRange": skxml.DblType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/GroundRange": skxml.DblType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/DopplerConeAngle": skxml.DblType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/GrazeAngle": skxml.DblType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/IncidenceAngle": skxml.DblType(),
        f"ReferenceGeometry/Bistatic/{d}Platform/AzimuthAngle": skxml.DblType(),
    }
TRANSCODERS |= {
    "Antenna/NumACFs": skxml.IntType(),
    "Antenna/NumAPCs": skxml.IntType(),
    "Antenna/NumAntPats": skxml.IntType(),
    "Antenna/AntCoordFrame/Identifier": skxml.TxtType(),
    "Antenna/AntCoordFrame/XAxisPoly": skxml.XyzPolyType(),
    "Antenna/AntCoordFrame/YAxisPoly": skxml.XyzPolyType(),
    "Antenna/AntCoordFrame/UseACFPVP": skxml.BoolType(),
    "Antenna/AntPhaseCenter/Identifier": skxml.TxtType(),
    "Antenna/AntPhaseCenter/ACFId": skxml.TxtType(),
    "Antenna/AntPhaseCenter/APCXYZ": skxml.XyzType(),
    "Antenna/AntPattern/Identifier": skxml.TxtType(),
    "Antenna/AntPattern/FreqZero": skxml.DblType(),
    "Antenna/AntPattern/GainZero": skxml.DblType(),
    "Antenna/AntPattern/EBFreqShift": skxml.BoolType(),
    "Antenna/AntPattern/EBFreqShiftSF/DCXSF": skxml.DblType(),
    "Antenna/AntPattern/EBFreqShiftSF/DCYSF": skxml.DblType(),
    "Antenna/AntPattern/MLFreqDilation": skxml.BoolType(),
    "Antenna/AntPattern/MLFreqDilationSF/DCXSF": skxml.DblType(),
    "Antenna/AntPattern/MLFreqDilationSF/DCYSF": skxml.DblType(),
    "Antenna/AntPattern/GainBSPoly": skxml.PolyType(),
    "Antenna/AntPattern/AntPolRef/AmpX": skxml.DblType(),
    "Antenna/AntPattern/AntPolRef/AmpY": skxml.DblType(),
    "Antenna/AntPattern/AntPolRef/PhaseY": skxml.DblType(),
    "Antenna/AntPattern/EB/DCXPoly": skxml.PolyType(),
    "Antenna/AntPattern/EB/DCYPoly": skxml.PolyType(),
    "Antenna/AntPattern/EB/UseEBPVP": skxml.BoolType(),
    "Antenna/AntPattern/Array/GainPoly": skxml.Poly2dType(),
    "Antenna/AntPattern/Array/PhasePoly": skxml.Poly2dType(),
    "Antenna/AntPattern/Array/AntGPId": skxml.TxtType(),
    "Antenna/AntPattern/Element/GainPoly": skxml.Poly2dType(),
    "Antenna/AntPattern/Element/PhasePoly": skxml.Poly2dType(),
    "Antenna/AntPattern/Element/AntGPId": skxml.TxtType(),
    "Antenna/AntPattern/GainPhaseArray/Freq": skxml.DblType(),
    "Antenna/AntPattern/GainPhaseArray/ArrayId": skxml.TxtType(),
    "Antenna/AntPattern/GainPhaseArray/ElementId": skxml.TxtType(),
}
TRANSCODERS |= {
    "TxRcv/NumTxWFs": skxml.IntType(),
    "TxRcv/TxWFParameters/Identifier": skxml.TxtType(),
    "TxRcv/TxWFParameters/PulseLength": skxml.DblType(),
    "TxRcv/TxWFParameters/RFBandwidth": skxml.DblType(),
    "TxRcv/TxWFParameters/FreqCenter": skxml.DblType(),
    "TxRcv/TxWFParameters/LFMRate": skxml.DblType(),
    "TxRcv/TxWFParameters/Polarization": skxml.TxtType(),
    "TxRcv/TxWFParameters/Power": skxml.DblType(),
    "TxRcv/NumRcvs": skxml.IntType(),
    "TxRcv/RcvParameters/Identifier": skxml.TxtType(),
    "TxRcv/RcvParameters/WindowLength": skxml.DblType(),
    "TxRcv/RcvParameters/SampleRate": skxml.DblType(),
    "TxRcv/RcvParameters/IFFilterBW": skxml.DblType(),
    "TxRcv/RcvParameters/FreqCenter": skxml.DblType(),
    "TxRcv/RcvParameters/LFMRate": skxml.DblType(),
    "TxRcv/RcvParameters/Polarization": skxml.TxtType(),
    "TxRcv/RcvParameters/PathGain": skxml.DblType(),
}


def _decorr_type(xml_path):
    return {f"{xml_path}/{x}": skxml.DblType() for x in ("CorrCoefZero", "DecorrRate")}


TRANSCODERS |= {
    "ErrorParameters/Monostatic/PosVelErr/Frame": skxml.TxtType(),
    "ErrorParameters/Monostatic/PosVelErr/P1": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/P2": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/P3": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/V1": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/V2": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/V3": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P1P2": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P1P3": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P1V1": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P1V2": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P1V3": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P2P3": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P2V1": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P2V2": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P2V3": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P3V1": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P3V2": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/P3V3": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/V1V2": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/V1V3": skxml.DblType(),
    "ErrorParameters/Monostatic/PosVelErr/CorrCoefs/V2V3": skxml.DblType(),
    **_decorr_type("ErrorParameters/Monostatic/PosVelErr/PositionDecorr"),
    "ErrorParameters/Monostatic/RadarSensor/RangeBias": skxml.DblType(),
    "ErrorParameters/Monostatic/RadarSensor/ClockFreqSF": skxml.DblType(),
    "ErrorParameters/Monostatic/RadarSensor/CollectionStartTime": skxml.DblType(),
    **_decorr_type("ErrorParameters/Monostatic/RadarSensor/RangeBiasDecorr"),
    "ErrorParameters/Monostatic/TropoError/TropoRangeVertical": skxml.DblType(),
    "ErrorParameters/Monostatic/TropoError/TropoRangeSlant": skxml.DblType(),
    **_decorr_type("ErrorParameters/Monostatic/TropoError/TropoRangeDecorr"),
    "ErrorParameters/Monostatic/IonoError/IonoRangeVertical": skxml.DblType(),
    "ErrorParameters/Monostatic/IonoError/IonoRangeRateVertical": skxml.DblType(),
    "ErrorParameters/Monostatic/IonoError/IonoRgRgRateCC": skxml.DblType(),
    **_decorr_type("ErrorParameters/Monostatic/IonoError/IonoRangeVertDecorr"),
    "ErrorParameters/Monostatic/AddedParameters/Parameter": skxml.ParameterType(),
    "ErrorParameters/Bistatic/AddedParameters/Parameter": skxml.ParameterType(),
}
for d in ("Tx", "Rcv"):
    TRANSCODERS |= {
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/Frame": skxml.TxtType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/P1": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/P2": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/P3": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/V1": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/V2": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/V3": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P1P2": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P1P3": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P1V1": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P1V2": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P1V3": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P2P3": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P2V1": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P2V2": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P2V3": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P3V1": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P3V2": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/P3V3": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/V1V2": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/V1V3": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/CorrCoefs/V2V3": skxml.DblType(),
        **_decorr_type(
            f"ErrorParameters/Bistatic/{d}Platform/PosVelErr/PositionDecorr"
        ),
        f"ErrorParameters/Bistatic/{d}Platform/RadarSensor/DelayBias": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/RadarSensor/ClockFreqSF": skxml.DblType(),
        f"ErrorParameters/Bistatic/{d}Platform/RadarSensor/CollectionStartTime": skxml.DblType(),
    }
TRANSCODERS |= {
    "ProductInfo/Profile": skxml.TxtType(),
    "ProductInfo/CreationInfo/Application": skxml.TxtType(),
    "ProductInfo/CreationInfo/DateTime": skxml.XdtType(),
    "ProductInfo/CreationInfo/Site": skxml.TxtType(),
    "ProductInfo/CreationInfo/Parameter": skxml.ParameterType(),
    "ProductInfo/Parameter": skxml.ParameterType(),
}
TRANSCODERS |= {
    "GeoInfo/Desc": skxml.ParameterType(),
    "GeoInfo/Point": skxml.LatLonType(),
    "GeoInfo/Line": skxml.ListType("Endpoint", skxml.LatLonType()),
    "GeoInfo/Polygon": skxml.ListType("Vertex", skxml.LatLonType()),
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
    XmlHelper for Compensated Phase History Data (CPHD).

    """

    _transcoders_ = TRANSCODERS

    def _get_simple_path(self, elem):
        return re.sub(r"(GeoInfo/)+", "GeoInfo/", super()._get_simple_path(elem))
