"""
========
CRSD XML
========

Functions from CRSD Design & Implementation Description Document.

"""

import re

import sarkit._xmlhelp as skxml
import sarkit.cphd as skcphd
import sarkit.standards.sicd.xml as sicd_xml

ImageAreaCornerPointsType = skcphd.ImageAreaCornerPointsType
PxpType = skcphd.PvpType
AddedPxpType = skcphd.AddedPvpType
MtxType = sicd_xml.MtxType


def _decorr_type(xml_path):
    return {f"{xml_path}/{x}": skxml.DblType() for x in ("CorrCoefZero", "DecorrRate")}


TRANSCODERS: dict[str, skxml.Type] = {
    "ProductInfo/ProductName": skxml.TxtType(),
    "ProductInfo/Classification": skxml.TxtType(),
    "ProductInfo/ReleaseInfo": skxml.TxtType(),
    "ProductInfo/CountryCode": skxml.TxtType(),
    "ProductInfo/Profile": skxml.TxtType(),
    "ProductInfo/CreationInfo/Application": skxml.TxtType(),
    "ProductInfo/CreationInfo/DateTime": skxml.XdtType(),
    "ProductInfo/CreationInfo/Site": skxml.TxtType(),
    "ProductInfo/CreationInfo/Parameter": skxml.ParameterType(),
    "ProductInfo/Parameter": skxml.ParameterType(),
}
TRANSCODERS |= {
    "SARInfo/CollectType": skxml.TxtType(),
    "SARInfo/RadarMode/ModeType": skxml.TxtType(),
    "SARInfo/RadarMode/ModeID": skxml.TxtType(),
    "SARInfo/Parameter": skxml.ParameterType(),
}
TRANSCODERS |= {
    "TransmitInfo/SensorName": skxml.TxtType(),
    "TransmitInfo/EventName": skxml.TxtType(),
    "TransmitInfo/Parameter": skxml.ParameterType(),
}
TRANSCODERS |= {
    "ReceiveInfo/SensorName": skxml.TxtType(),
    "ReceiveInfo/EventName": skxml.TxtType(),
    "ReceiveInfo/Parameter": skxml.ParameterType(),
}
TRANSCODERS |= {
    "Global/CollectionRefTime": skxml.XdtType(),
    "Global/TropoParameters/N0": skxml.DblType(),
    "Global/TropoParameters/RefHeight": skxml.TxtType(),
    "Global/TropoParameters/N0ErrorStdDev": skxml.DblType(),
    "Global/IonoParameters/TECV": skxml.DblType(),
    "Global/IonoParameters/F2Height": skxml.DblType(),
    "Global/IonoParameters/TECVErrorStdDev": skxml.DblType(),
    "Global/Transmit/TxTime1": skxml.DblType(),
    "Global/Transmit/TxTime2": skxml.DblType(),
    "Global/Transmit/FxMin": skxml.DblType(),
    "Global/Transmit/FxMax": skxml.DblType(),
    "Global/Receive/RcvStartTime1": skxml.DblType(),
    "Global/Receive/RcvStartTime2": skxml.DblType(),
    "Global/Receive/FrcvMin": skxml.DblType(),
    "Global/Receive/FrcvMax": skxml.DblType(),
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
    "Data/Support/NumSupportArrays": skxml.IntType(),
    "Data/Support/SupportArray/Identifier": skxml.TxtType(),
    "Data/Support/SupportArray/NumRows": skxml.IntType(),
    "Data/Support/SupportArray/NumCols": skxml.IntType(),
    "Data/Support/SupportArray/BytesPerElement": skxml.IntType(),
    "Data/Support/SupportArray/ArrayByteOffset": skxml.IntType(),
    "Data/Transmit/NumBytesPPP": skxml.IntType(),
    "Data/Transmit/NumTxSequences": skxml.IntType(),
    "Data/Transmit/TxSequence/Identifier": skxml.TxtType(),
    "Data/Transmit/TxSequence/NumPulses": skxml.IntType(),
    "Data/Transmit/TxSequence/PPPArrayByteOffset": skxml.IntType(),
    "Data/Receive/SignalArrayFormat": skxml.TxtType(),
    "Data/Receive/NumBytesPVP": skxml.IntType(),
    "Data/Receive/NumCRSDChannels": skxml.IntType(),
    "Data/Receive/SignalCompression/Identifier": skxml.TxtType(),
    "Data/Receive/SignalCompression/CompressedSignalSize": skxml.IntType(),
    "Data/Receive/SignalCompression/Processing/Type": skxml.TxtType(),
    "Data/Receive/SignalCompression/Processing/Parameter": skxml.ParameterType(),
    "Data/Receive/Channel/Identifier": skxml.TxtType(),
    "Data/Receive/Channel/NumVectors": skxml.IntType(),
    "Data/Receive/Channel/NumSamples": skxml.IntType(),
    "Data/Receive/Channel/SignalArrayByteOffset": skxml.IntType(),
    "Data/Receive/Channel/PVPArrayByteOffset": skxml.IntType(),
}
TRANSCODERS |= {
    "TxSequence/RefTxID": skxml.TxtType(),
    "TxSequence/TxWFType": skxml.TxtType(),
    "TxSequence/Parameters/Identifier": skxml.TxtType(),
    "TxSequence/Parameters/RefPulseIndex": skxml.IntType(),
    "TxSequence/Parameters/XMId": skxml.TxtType(),
    "TxSequence/Parameters/FxResponseId": skxml.TxtType(),
    "TxSequence/Parameters/FxBWFixed": skxml.BoolType(),
    "TxSequence/Parameters/FxC": skxml.DblType(),
    "TxSequence/Parameters/FxBW": skxml.DblType(),
    "TxSequence/Parameters/TXmtMin": skxml.DblType(),
    "TxSequence/Parameters/TXmtMax": skxml.DblType(),
    "TxSequence/Parameters/TxTime1": skxml.DblType(),
    "TxSequence/Parameters/TxTime2": skxml.DblType(),
    "TxSequence/Parameters/TxAPCId": skxml.TxtType(),
    "TxSequence/Parameters/TxAPATId": skxml.TxtType(),
    "TxSequence/Parameters/TxRefPoint/ECF": skxml.XyzType(),
    "TxSequence/Parameters/TxRefPoint/IAC": skxml.XyType(),
    "TxSequence/Parameters/TxPolarization/PolarizationID": skxml.TxtType(),
    "TxSequence/Parameters/TxPolarization/AmpH": skxml.DblType(),
    "TxSequence/Parameters/TxPolarization/AmpV": skxml.DblType(),
    "TxSequence/Parameters/TxPolarization/PhaseH": skxml.DblType(),
    "TxSequence/Parameters/TxPolarization/PhaseV": skxml.DblType(),
    "TxSequence/Parameters/TxRefRadIntensity": skxml.DblType(),
    "TxSequence/Parameters/TxRadIntErrorStdDev": skxml.DblType(),
    "TxSequence/Parameters/TxRefLAtm": skxml.DblType(),
    "TxSequence/Parameters/Parameter": skxml.ParameterType(),
}
TRANSCODERS |= {
    "Channel/RefChId": skxml.TxtType(),
    "Channel/Parameters/Identifier": skxml.TxtType(),
    "Channel/Parameters/RefVectorIndex": skxml.IntType(),
    "Channel/Parameters/RefFreqFixed": skxml.BoolType(),
    "Channel/Parameters/FrcvFixed": skxml.BoolType(),
    "Channel/Parameters/SignalNormal": skxml.BoolType(),
    "Channel/Parameters/F0Ref": skxml.DblType(),
    "Channel/Parameters/Fs": skxml.DblType(),
    "Channel/Parameters/BWInst": skxml.DblType(),
    "Channel/Parameters/RcvStartTime1": skxml.DblType(),
    "Channel/Parameters/RcvStartTime2": skxml.DblType(),
    "Channel/Parameters/FrcvMin": skxml.DblType(),
    "Channel/Parameters/FrcvMax": skxml.DblType(),
    "Channel/Parameters/RcvAPCId": skxml.TxtType(),
    "Channel/Parameters/RcvAPATId": skxml.TxtType(),
    "Channel/Parameters/RcvRefPoint/ECF": skxml.XyzType(),
    "Channel/Parameters/RcvRefPoint/IAC": skxml.XyType(),
    "Channel/Parameters/RcvPolarization/PolarizationID": skxml.TxtType(),
    "Channel/Parameters/RcvPolarization/AmpH": skxml.DblType(),
    "Channel/Parameters/RcvPolarization/AmpV": skxml.DblType(),
    "Channel/Parameters/RcvPolarization/PhaseH": skxml.DblType(),
    "Channel/Parameters/RcvPolarization/PhaseV": skxml.DblType(),
    "Channel/Parameters/RcvRefIrradiance": skxml.DblType(),
    "Channel/Parameters/RcvIrradianceErrorStdDev": skxml.DblType(),
    "Channel/Parameters/RcvRefLAtm": skxml.DblType(),
    "Channel/Parameters/PNCRSD": skxml.DblType(),
    "Channel/Parameters/BNCRSD": skxml.DblType(),
    "Channel/Parameters/Parameter": skxml.ParameterType(),
    "Channel/Parameters/SARImage/TxId": skxml.TxtType(),
    "Channel/Parameters/SARImage/RefVectorPulseIndex": skxml.IntType(),
    "Channel/Parameters/SARImage/TxPolarization/PolarizationID": skxml.TxtType(),
    "Channel/Parameters/SARImage/TxPolarization/AmpH": skxml.DblType(),
    "Channel/Parameters/SARImage/TxPolarization/AmpV": skxml.DblType(),
    "Channel/Parameters/SARImage/TxPolarization/PhaseH": skxml.DblType(),
    "Channel/Parameters/SARImage/TxPolarization/PhaseV": skxml.DblType(),
    "Channel/Parameters/SARImage/DwellTimes/Polynomials/CODId": skxml.TxtType(),
    "Channel/Parameters/SARImage/DwellTimes/Polynomials/DwellId": skxml.TxtType(),
    "Channel/Parameters/SARImage/DwellTimes/Array/DTAId": skxml.TxtType(),
    "Channel/Parameters/SARImage/ImageArea/X1Y1": skxml.XyType(),
    "Channel/Parameters/SARImage/ImageArea/X2Y2": skxml.XyType(),
    "Channel/Parameters/SARImage/ImageArea/Polygon": skxml.ListType(
        "Vertex", skxml.XyType()
    ),
}
TRANSCODERS |= {
    "ReferenceGeometry/RefPoint/ECF": skxml.XyzType(),
    "ReferenceGeometry/RefPoint/IAC": skxml.XyType(),
    "ReferenceGeometry/SARImage/CODTime": skxml.DblType(),
    "ReferenceGeometry/SARImage/DwellTime": skxml.DblType(),
    "ReferenceGeometry/SARImage/ReferenceTime": skxml.DblType(),
    "ReferenceGeometry/SARImage/ARPPos": skxml.XyzType(),
    "ReferenceGeometry/SARImage/ARPVel": skxml.XyzType(),
    "ReferenceGeometry/SARImage/BistaticAngle": skxml.DblType(),
    "ReferenceGeometry/SARImage/BistaticAngleRate": skxml.DblType(),
    "ReferenceGeometry/SARImage/SideOfTrack": skxml.TxtType(),
    "ReferenceGeometry/SARImage/SlantRange": skxml.DblType(),
    "ReferenceGeometry/SARImage/GroundRange": skxml.DblType(),
    "ReferenceGeometry/SARImage/DopplerConeAngle": skxml.DblType(),
    "ReferenceGeometry/SARImage/SquintAngle": skxml.DblType(),
    "ReferenceGeometry/SARImage/AzimuthAngle": skxml.DblType(),
    "ReferenceGeometry/SARImage/GrazeAngle": skxml.DblType(),
    "ReferenceGeometry/SARImage/IncidenceAngle": skxml.DblType(),
    "ReferenceGeometry/SARImage/TwistAngle": skxml.DblType(),
    "ReferenceGeometry/SARImage/SlopeAngle": skxml.DblType(),
    "ReferenceGeometry/SARImage/LayoverAngle": skxml.DblType(),
}
for d in ("Tx", "Rcv"):
    TRANSCODERS |= {
        f"ReferenceGeometry/{d}Parameters/Time": skxml.DblType(),
        f"ReferenceGeometry/{d}Parameters/APCPos": skxml.XyzType(),
        f"ReferenceGeometry/{d}Parameters/APCVel": skxml.XyzType(),
        f"ReferenceGeometry/{d}Parameters/SideOfTrack": skxml.TxtType(),
        f"ReferenceGeometry/{d}Parameters/SlantRange": skxml.DblType(),
        f"ReferenceGeometry/{d}Parameters/GroundRange": skxml.DblType(),
        f"ReferenceGeometry/{d}Parameters/DopplerConeAngle": skxml.DblType(),
        f"ReferenceGeometry/{d}Parameters/SquintAngle": skxml.DblType(),
        f"ReferenceGeometry/{d}Parameters/AzimuthAngle": skxml.DblType(),
        f"ReferenceGeometry/{d}Parameters/GrazeAngle": skxml.DblType(),
        f"ReferenceGeometry/{d}Parameters/IncidenceAngle": skxml.DblType(),
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
    "SupportArray/AntGainPhase/Identifier": skxml.TxtType(),
    "SupportArray/AntGainPhase/ElementFormat": skxml.TxtType(),
    "SupportArray/AntGainPhase/X0": skxml.DblType(),
    "SupportArray/AntGainPhase/Y0": skxml.DblType(),
    "SupportArray/AntGainPhase/XSS": skxml.DblType(),
    "SupportArray/AntGainPhase/YSS": skxml.DblType(),
    "SupportArray/AntGainPhase/NODATA": skxml.HexType(),
    "SupportArray/FxResponseArray/Identifier": skxml.TxtType(),
    "SupportArray/FxResponseArray/ElementFormat": skxml.TxtType(),
    "SupportArray/FxResponseArray/Fx0FXR": skxml.DblType(),
    "SupportArray/FxResponseArray/FxSSFXR": skxml.DblType(),
    "SupportArray/XMArray/Identifier": skxml.TxtType(),
    "SupportArray/XMArray/ElementFormat": skxml.TxtType(),
    "SupportArray/XMArray/TsXMA": skxml.DblType(),
    "SupportArray/XMArray/MaxXMBW": skxml.DblType(),
    "SupportArray/DwellTimeArray/Identifier": skxml.TxtType(),
    "SupportArray/DwellTimeArray/ElementFormat": skxml.TxtType(),
    "SupportArray/DwellTimeArray/X0": skxml.DblType(),
    "SupportArray/DwellTimeArray/Y0": skxml.DblType(),
    "SupportArray/DwellTimeArray/XSS": skxml.DblType(),
    "SupportArray/DwellTimeArray/YSS": skxml.DblType(),
    "SupportArray/DwellTimeArray/NODATA": skxml.HexType(),
    "SupportArray/IAZArray/Identifier": skxml.TxtType(),
    "SupportArray/IAZArray/ElementFormat": skxml.TxtType(),
    "SupportArray/IAZArray/X0": skxml.DblType(),
    "SupportArray/IAZArray/Y0": skxml.DblType(),
    "SupportArray/IAZArray/XSS": skxml.DblType(),
    "SupportArray/IAZArray/YSS": skxml.DblType(),
    "SupportArray/IAZArray/NODATA": skxml.HexType(),
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
    "PPP/TxTime": PxpType(),
    "PPP/TxPos": PxpType(),
    "PPP/TxVel": PxpType(),
    "PPP/FX1": PxpType(),
    "PPP/FX2": PxpType(),
    "PPP/TXmt": PxpType(),
    "PPP/PhiX0": PxpType(),
    "PPP/FxFreq0": PxpType(),
    "PPP/FxRate": PxpType(),
    "PPP/TxRadInt": PxpType(),
    "PPP/TxACX": PxpType(),
    "PPP/TxACY": PxpType(),
    "PPP/TxEB": PxpType(),
    "PPP/FxResponseIndex": PxpType(),
    "PPP/XMIndex": PxpType(),
    "PPP/AddedPPP": AddedPxpType(),
}
TRANSCODERS |= {
    "PVP/RcvStart": PxpType(),
    "PVP/RcvPos": PxpType(),
    "PVP/RcvVel": PxpType(),
    "PVP/FRCV1": PxpType(),
    "PVP/FRCV2": PxpType(),
    "PVP/RefPhi0": PxpType(),
    "PVP/RefFreq": PxpType(),
    "PVP/DFIC0": PxpType(),
    "PVP/FICRate": PxpType(),
    "PVP/RcvACX": PxpType(),
    "PVP/RcvACY": PxpType(),
    "PVP/RcvEB": PxpType(),
    "PVP/SIGNAL": PxpType(),
    "PVP/AmpSF": PxpType(),
    "PVP/DGRGC": PxpType(),
    "PVP/TxPulseIndex": PxpType(),
    "PVP/AddedPVP": AddedPxpType(),
}
TRANSCODERS |= {
    "Antenna/NumACFs": skxml.IntType(),
    "Antenna/NumAPCs": skxml.IntType(),
    "Antenna/NumAntPats": skxml.IntType(),
    "Antenna/AntCoordFrame/Identifier": skxml.TxtType(),
    "Antenna/AntPhaseCenter/Identifier": skxml.TxtType(),
    "Antenna/AntPhaseCenter/ACFId": skxml.TxtType(),
    "Antenna/AntPhaseCenter/APCXYZ": skxml.XyzType(),
    "Antenna/AntPattern/Identifier": skxml.TxtType(),
    "Antenna/AntPattern/FreqZero": skxml.DblType(),
    "Antenna/AntPattern/ArrayGPId": skxml.TxtType(),
    "Antenna/AntPattern/ElementGPId": skxml.TxtType(),
    "Antenna/AntPattern/EBFreqShift/DCXSF": skxml.DblType(),
    "Antenna/AntPattern/EBFreqShift/DCYSF": skxml.DblType(),
    "Antenna/AntPattern/MLFreqDilation/DCXSF": skxml.DblType(),
    "Antenna/AntPattern/MLFreqDilation/DCYSF": skxml.DblType(),
    "Antenna/AntPattern/GainBSPoly": skxml.PolyType(),
    "Antenna/AntPattern/AntPolRef/AmpX": skxml.DblType(),
    "Antenna/AntPattern/AntPolRef/AmpY": skxml.DblType(),
    "Antenna/AntPattern/AntPolRef/PhaseX": skxml.DblType(),
    "Antenna/AntPattern/AntPolRef/PhaseY": skxml.DblType(),
}
TRANSCODERS |= {
    "ErrorParameters/SARImage/Monostatic/PosVelError/Frame": skxml.TxtType(),
    "ErrorParameters/SARImage/Monostatic/PosVelError/PVCov": MtxType((6, 6)),
    **_decorr_type("ErrorParameters/SARImage/Monostatic/PosVelError/PosDecorr"),
    "ErrorParameters/SARImage/Monostatic/RadarSensor/TimeFreqCov": MtxType((3, 3)),
    **_decorr_type(
        "ErrorParameters/SARImage/Monostatic/RadarSensor/TimeFreqDecorr/TxTimeDecorr"
    ),
    **_decorr_type(
        "ErrorParameters/SARImage/Monostatic/RadarSensor/TimeFreqDecorr/RcvTimeDecorr"
    ),
    **_decorr_type(
        "ErrorParameters/SARImage/Monostatic/RadarSensor/TimeFreqDecorr/ClockFreqDecorr"
    ),
    "ErrorParameters/SARImage/Bistatic/PosVelError/TxFrame": skxml.TxtType(),
    "ErrorParameters/SARImage/Bistatic/PosVelError/TxPVCov": MtxType((6, 6)),
    "ErrorParameters/SARImage/Bistatic/PosVelError/RcvFrame": skxml.TxtType(),
    "ErrorParameters/SARImage/Bistatic/PosVelError/RcvPVCov": MtxType((6, 6)),
    "ErrorParameters/SARImage/Bistatic/PosVelError/TxRcvPVCov": MtxType((6, 6)),
    **_decorr_type(
        "ErrorParameters/SARImage/Bistatic/PosVelError/PosVelDecorr/TxPosDecorr"
    ),
    **_decorr_type(
        "ErrorParameters/SARImage/Bistatic/PosVelError/PosVelDecorr/RcvPosDecorr"
    ),
    "ErrorParameters/SARImage/Bistatic/RadarSensor/TimeFreqCov": MtxType((4, 4)),
    **_decorr_type(
        "ErrorParameters/SARImage/Bistatic/RadarSensor/TimeFreqDecorr/TxTimeDecorr"
    ),
    **_decorr_type(
        "ErrorParameters/SARImage/Bistatic/RadarSensor/TimeFreqDecorr/RcvTimeDecorr"
    ),
    **_decorr_type(
        "ErrorParameters/SARImage/Bistatic/RadarSensor/TimeFreqDecorr/TxClockFreqDecorr"
    ),
    **_decorr_type(
        "ErrorParameters/SARImage/Bistatic/RadarSensor/TimeFreqDecorr/RcvClockFreqDecorr"
    ),
}
for d in ("Tx", "Rcv"):
    TRANSCODERS |= {
        f"ErrorParameters/{d}Sensor/PosVelError/Frame": skxml.TxtType(),
        f"ErrorParameters/{d}Sensor/PosVelError/PVCov": MtxType((6, 6)),
        **_decorr_type(f"ErrorParameters/{d}Sensor/PosVelError/PosDecorr"),
        f"ErrorParameters/{d}Sensor/RadarSensor/TimeFreqCov": MtxType((2, 2)),
        **_decorr_type(
            f"ErrorParameters/{d}Sensor/RadarSensor/TimeFreqDecorr/TimeDecorr"
        ),
        **_decorr_type(
            f"ErrorParameters/{d}Sensor/RadarSensor/TimeFreqDecorr/ClockFreqDecorr"
        ),
    }
TRANSCODERS |= {
    "GeoInfo/Desc": skxml.ParameterType(),
    "GeoInfo/Point": skxml.LatLonType(),
    "GeoInfo/Line": skxml.ListType("Endpoint", skxml.LatLonType()),
    "GeoInfo/Polygon": skxml.ListType("Vertex", skxml.LatLonType()),
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
    XmlHelper for Compensated Radar Signal Data (CRSD).

    """

    _transcoders_ = TRANSCODERS

    def _get_simple_path(self, elem):
        return re.sub(r"(GeoInfo/)+", "GeoInfo/", super()._get_simple_path(elem))
