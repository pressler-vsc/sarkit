"""
========
CRSD XML
========

Functions from CRSD Design & Implementation Description Document.

"""

import re

import sarkit.standards.cphd.xml as cphd_xml
import sarkit.standards.sicd.xml as sicd_xml
import sarkit.standards.xml as ssxml

ImageAreaCornerPointsType = cphd_xml.ImageAreaCornerPointsType
PxpType = cphd_xml.PvpType
AddedPxpType = cphd_xml.AddedPvpType
MtxType = sicd_xml.MtxType


def _decorr_type(xml_path):
    return {f"{xml_path}/{x}": ssxml.DblType() for x in ("CorrCoefZero", "DecorrRate")}


TRANSCODERS: dict[str, ssxml.Type] = {
    "ProductInfo/ProductName": ssxml.TxtType(),
    "ProductInfo/Classification": ssxml.TxtType(),
    "ProductInfo/ReleaseInfo": ssxml.TxtType(),
    "ProductInfo/CountryCode": ssxml.TxtType(),
    "ProductInfo/Profile": ssxml.TxtType(),
    "ProductInfo/CreationInfo/Application": ssxml.TxtType(),
    "ProductInfo/CreationInfo/DateTime": ssxml.XdtType(),
    "ProductInfo/CreationInfo/Site": ssxml.TxtType(),
    "ProductInfo/CreationInfo/Parameter": ssxml.ParameterType(),
    "ProductInfo/Parameter": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "SARInfo/CollectType": ssxml.TxtType(),
    "SARInfo/RadarMode/ModeType": ssxml.TxtType(),
    "SARInfo/RadarMode/ModeID": ssxml.TxtType(),
    "SARInfo/Parameter": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "TransmitInfo/SensorName": ssxml.TxtType(),
    "TransmitInfo/EventName": ssxml.TxtType(),
    "TransmitInfo/Parameter": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "ReceiveInfo/SensorName": ssxml.TxtType(),
    "ReceiveInfo/EventName": ssxml.TxtType(),
    "ReceiveInfo/Parameter": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "Global/CollectionRefTime": ssxml.XdtType(),
    "Global/TropoParameters/N0": ssxml.DblType(),
    "Global/TropoParameters/RefHeight": ssxml.TxtType(),
    "Global/TropoParameters/N0ErrorStdDev": ssxml.DblType(),
    "Global/IonoParameters/TECV": ssxml.DblType(),
    "Global/IonoParameters/F2Height": ssxml.DblType(),
    "Global/IonoParameters/TECVErrorStdDev": ssxml.DblType(),
    "Global/Transmit/TxTime1": ssxml.DblType(),
    "Global/Transmit/TxTime2": ssxml.DblType(),
    "Global/Transmit/FxMin": ssxml.DblType(),
    "Global/Transmit/FxMax": ssxml.DblType(),
    "Global/Receive/RcvStartTime1": ssxml.DblType(),
    "Global/Receive/RcvStartTime2": ssxml.DblType(),
    "Global/Receive/FrcvMin": ssxml.DblType(),
    "Global/Receive/FrcvMax": ssxml.DblType(),
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
    "Data/Support/NumSupportArrays": ssxml.IntType(),
    "Data/Support/SupportArray/Identifier": ssxml.TxtType(),
    "Data/Support/SupportArray/NumRows": ssxml.IntType(),
    "Data/Support/SupportArray/NumCols": ssxml.IntType(),
    "Data/Support/SupportArray/BytesPerElement": ssxml.IntType(),
    "Data/Support/SupportArray/ArrayByteOffset": ssxml.IntType(),
    "Data/Transmit/NumBytesPPP": ssxml.IntType(),
    "Data/Transmit/NumTxSequences": ssxml.IntType(),
    "Data/Transmit/TxSequence/Identifier": ssxml.TxtType(),
    "Data/Transmit/TxSequence/NumPulses": ssxml.IntType(),
    "Data/Transmit/TxSequence/PPPArrayByteOffset": ssxml.IntType(),
    "Data/Receive/SignalArrayFormat": ssxml.TxtType(),
    "Data/Receive/NumBytesPVP": ssxml.IntType(),
    "Data/Receive/NumCRSDChannels": ssxml.IntType(),
    "Data/Receive/SignalCompression/Identifier": ssxml.TxtType(),
    "Data/Receive/SignalCompression/CompressedSignalSize": ssxml.IntType(),
    "Data/Receive/SignalCompression/Processing/Type": ssxml.TxtType(),
    "Data/Receive/SignalCompression/Processing/Parameter": ssxml.ParameterType(),
    "Data/Receive/Channel/Identifier": ssxml.TxtType(),
    "Data/Receive/Channel/NumVectors": ssxml.IntType(),
    "Data/Receive/Channel/NumSamples": ssxml.IntType(),
    "Data/Receive/Channel/SignalArrayByteOffset": ssxml.IntType(),
    "Data/Receive/Channel/PVPArrayByteOffset": ssxml.IntType(),
}
TRANSCODERS |= {
    "TxSequence/RefTxID": ssxml.TxtType(),
    "TxSequence/TxWFType": ssxml.TxtType(),
    "TxSequence/Parameters/Identifier": ssxml.TxtType(),
    "TxSequence/Parameters/RefPulseIndex": ssxml.IntType(),
    "TxSequence/Parameters/XMId": ssxml.TxtType(),
    "TxSequence/Parameters/FxResponseId": ssxml.TxtType(),
    "TxSequence/Parameters/FxBWFixed": ssxml.BoolType(),
    "TxSequence/Parameters/FxC": ssxml.DblType(),
    "TxSequence/Parameters/FxBW": ssxml.DblType(),
    "TxSequence/Parameters/TXmtMin": ssxml.DblType(),
    "TxSequence/Parameters/TXmtMax": ssxml.DblType(),
    "TxSequence/Parameters/TxTime1": ssxml.DblType(),
    "TxSequence/Parameters/TxTime2": ssxml.DblType(),
    "TxSequence/Parameters/TxAPCId": ssxml.TxtType(),
    "TxSequence/Parameters/TxAPATId": ssxml.TxtType(),
    "TxSequence/Parameters/TxRefPoint/ECF": ssxml.XyzType(),
    "TxSequence/Parameters/TxRefPoint/IAC": ssxml.XyType(),
    "TxSequence/Parameters/TxPolarization/PolarizationID": ssxml.TxtType(),
    "TxSequence/Parameters/TxPolarization/AmpH": ssxml.DblType(),
    "TxSequence/Parameters/TxPolarization/AmpV": ssxml.DblType(),
    "TxSequence/Parameters/TxPolarization/PhaseH": ssxml.DblType(),
    "TxSequence/Parameters/TxPolarization/PhaseV": ssxml.DblType(),
    "TxSequence/Parameters/TxRefRadIntensity": ssxml.DblType(),
    "TxSequence/Parameters/TxRadIntErrorStdDev": ssxml.DblType(),
    "TxSequence/Parameters/TxRefLAtm": ssxml.DblType(),
    "TxSequence/Parameters/Parameter": ssxml.ParameterType(),
}
TRANSCODERS |= {
    "Channel/RefChId": ssxml.TxtType(),
    "Channel/Parameters/Identifier": ssxml.TxtType(),
    "Channel/Parameters/RefVectorIndex": ssxml.IntType(),
    "Channel/Parameters/RefFreqFixed": ssxml.BoolType(),
    "Channel/Parameters/FrcvFixed": ssxml.BoolType(),
    "Channel/Parameters/SignalNormal": ssxml.BoolType(),
    "Channel/Parameters/F0Ref": ssxml.DblType(),
    "Channel/Parameters/Fs": ssxml.DblType(),
    "Channel/Parameters/BWInst": ssxml.DblType(),
    "Channel/Parameters/RcvStartTime1": ssxml.DblType(),
    "Channel/Parameters/RcvStartTime2": ssxml.DblType(),
    "Channel/Parameters/FrcvMin": ssxml.DblType(),
    "Channel/Parameters/FrcvMax": ssxml.DblType(),
    "Channel/Parameters/RcvAPCId": ssxml.TxtType(),
    "Channel/Parameters/RcvAPATId": ssxml.TxtType(),
    "Channel/Parameters/RcvRefPoint/ECF": ssxml.XyzType(),
    "Channel/Parameters/RcvRefPoint/IAC": ssxml.XyType(),
    "Channel/Parameters/RcvPolarization/PolarizationID": ssxml.TxtType(),
    "Channel/Parameters/RcvPolarization/AmpH": ssxml.DblType(),
    "Channel/Parameters/RcvPolarization/AmpV": ssxml.DblType(),
    "Channel/Parameters/RcvPolarization/PhaseH": ssxml.DblType(),
    "Channel/Parameters/RcvPolarization/PhaseV": ssxml.DblType(),
    "Channel/Parameters/RcvRefIrradiance": ssxml.DblType(),
    "Channel/Parameters/RcvIrradianceErrorStdDev": ssxml.DblType(),
    "Channel/Parameters/RcvRefLAtm": ssxml.DblType(),
    "Channel/Parameters/PNCRSD": ssxml.DblType(),
    "Channel/Parameters/BNCRSD": ssxml.DblType(),
    "Channel/Parameters/Parameter": ssxml.ParameterType(),
    "Channel/Parameters/SARImage/TxId": ssxml.TxtType(),
    "Channel/Parameters/SARImage/RefVectorPulseIndex": ssxml.IntType(),
    "Channel/Parameters/SARImage/TxPolarization/PolarizationID": ssxml.TxtType(),
    "Channel/Parameters/SARImage/TxPolarization/AmpH": ssxml.DblType(),
    "Channel/Parameters/SARImage/TxPolarization/AmpV": ssxml.DblType(),
    "Channel/Parameters/SARImage/TxPolarization/PhaseH": ssxml.DblType(),
    "Channel/Parameters/SARImage/TxPolarization/PhaseV": ssxml.DblType(),
    "Channel/Parameters/SARImage/DwellTimes/Polynomials/CODId": ssxml.TxtType(),
    "Channel/Parameters/SARImage/DwellTimes/Polynomials/DwellId": ssxml.TxtType(),
    "Channel/Parameters/SARImage/DwellTimes/Array/DTAId": ssxml.TxtType(),
    "Channel/Parameters/SARImage/ImageArea/X1Y1": ssxml.XyType(),
    "Channel/Parameters/SARImage/ImageArea/X2Y2": ssxml.XyType(),
    "Channel/Parameters/SARImage/ImageArea/Polygon": ssxml.ListType(
        "Vertex", ssxml.XyType()
    ),
}
TRANSCODERS |= {
    "ReferenceGeometry/RefPoint/ECF": ssxml.XyzType(),
    "ReferenceGeometry/RefPoint/IAC": ssxml.XyType(),
    "ReferenceGeometry/SARImage/CODTime": ssxml.DblType(),
    "ReferenceGeometry/SARImage/DwellTime": ssxml.DblType(),
    "ReferenceGeometry/SARImage/ReferenceTime": ssxml.DblType(),
    "ReferenceGeometry/SARImage/ARPPos": ssxml.XyzType(),
    "ReferenceGeometry/SARImage/ARPVel": ssxml.XyzType(),
    "ReferenceGeometry/SARImage/BistaticAngle": ssxml.DblType(),
    "ReferenceGeometry/SARImage/BistaticAngleRate": ssxml.DblType(),
    "ReferenceGeometry/SARImage/SideOfTrack": ssxml.TxtType(),
    "ReferenceGeometry/SARImage/SlantRange": ssxml.DblType(),
    "ReferenceGeometry/SARImage/GroundRange": ssxml.DblType(),
    "ReferenceGeometry/SARImage/DopplerConeAngle": ssxml.DblType(),
    "ReferenceGeometry/SARImage/SquintAngle": ssxml.DblType(),
    "ReferenceGeometry/SARImage/AzimuthAngle": ssxml.DblType(),
    "ReferenceGeometry/SARImage/GrazeAngle": ssxml.DblType(),
    "ReferenceGeometry/SARImage/IncidenceAngle": ssxml.DblType(),
    "ReferenceGeometry/SARImage/TwistAngle": ssxml.DblType(),
    "ReferenceGeometry/SARImage/SlopeAngle": ssxml.DblType(),
    "ReferenceGeometry/SARImage/LayoverAngle": ssxml.DblType(),
}
for d in ("Tx", "Rcv"):
    TRANSCODERS |= {
        f"ReferenceGeometry/{d}Parameters/Time": ssxml.DblType(),
        f"ReferenceGeometry/{d}Parameters/APCPos": ssxml.XyzType(),
        f"ReferenceGeometry/{d}Parameters/APCVel": ssxml.XyzType(),
        f"ReferenceGeometry/{d}Parameters/SideOfTrack": ssxml.TxtType(),
        f"ReferenceGeometry/{d}Parameters/SlantRange": ssxml.DblType(),
        f"ReferenceGeometry/{d}Parameters/GroundRange": ssxml.DblType(),
        f"ReferenceGeometry/{d}Parameters/DopplerConeAngle": ssxml.DblType(),
        f"ReferenceGeometry/{d}Parameters/SquintAngle": ssxml.DblType(),
        f"ReferenceGeometry/{d}Parameters/AzimuthAngle": ssxml.DblType(),
        f"ReferenceGeometry/{d}Parameters/GrazeAngle": ssxml.DblType(),
        f"ReferenceGeometry/{d}Parameters/IncidenceAngle": ssxml.DblType(),
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
    "SupportArray/AntGainPhase/Identifier": ssxml.TxtType(),
    "SupportArray/AntGainPhase/ElementFormat": ssxml.TxtType(),
    "SupportArray/AntGainPhase/X0": ssxml.DblType(),
    "SupportArray/AntGainPhase/Y0": ssxml.DblType(),
    "SupportArray/AntGainPhase/XSS": ssxml.DblType(),
    "SupportArray/AntGainPhase/YSS": ssxml.DblType(),
    "SupportArray/AntGainPhase/NODATA": ssxml.HexType(),
    "SupportArray/FxResponseArray/Identifier": ssxml.TxtType(),
    "SupportArray/FxResponseArray/ElementFormat": ssxml.TxtType(),
    "SupportArray/FxResponseArray/Fx0FXR": ssxml.DblType(),
    "SupportArray/FxResponseArray/FxSSFXR": ssxml.DblType(),
    "SupportArray/XMArray/Identifier": ssxml.TxtType(),
    "SupportArray/XMArray/ElementFormat": ssxml.TxtType(),
    "SupportArray/XMArray/TsXMA": ssxml.DblType(),
    "SupportArray/XMArray/MaxXMBW": ssxml.DblType(),
    "SupportArray/DwellTimeArray/Identifier": ssxml.TxtType(),
    "SupportArray/DwellTimeArray/ElementFormat": ssxml.TxtType(),
    "SupportArray/DwellTimeArray/X0": ssxml.DblType(),
    "SupportArray/DwellTimeArray/Y0": ssxml.DblType(),
    "SupportArray/DwellTimeArray/XSS": ssxml.DblType(),
    "SupportArray/DwellTimeArray/YSS": ssxml.DblType(),
    "SupportArray/DwellTimeArray/NODATA": ssxml.HexType(),
    "SupportArray/IAZArray/Identifier": ssxml.TxtType(),
    "SupportArray/IAZArray/ElementFormat": ssxml.TxtType(),
    "SupportArray/IAZArray/X0": ssxml.DblType(),
    "SupportArray/IAZArray/Y0": ssxml.DblType(),
    "SupportArray/IAZArray/XSS": ssxml.DblType(),
    "SupportArray/IAZArray/YSS": ssxml.DblType(),
    "SupportArray/IAZArray/NODATA": ssxml.HexType(),
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
    "Antenna/NumACFs": ssxml.IntType(),
    "Antenna/NumAPCs": ssxml.IntType(),
    "Antenna/NumAntPats": ssxml.IntType(),
    "Antenna/AntCoordFrame/Identifier": ssxml.TxtType(),
    "Antenna/AntPhaseCenter/Identifier": ssxml.TxtType(),
    "Antenna/AntPhaseCenter/ACFId": ssxml.TxtType(),
    "Antenna/AntPhaseCenter/APCXYZ": ssxml.XyzType(),
    "Antenna/AntPattern/Identifier": ssxml.TxtType(),
    "Antenna/AntPattern/FreqZero": ssxml.DblType(),
    "Antenna/AntPattern/ArrayGPId": ssxml.TxtType(),
    "Antenna/AntPattern/ElementGPId": ssxml.TxtType(),
    "Antenna/AntPattern/EBFreqShift/DCXSF": ssxml.DblType(),
    "Antenna/AntPattern/EBFreqShift/DCYSF": ssxml.DblType(),
    "Antenna/AntPattern/MLFreqDilation/DCXSF": ssxml.DblType(),
    "Antenna/AntPattern/MLFreqDilation/DCYSF": ssxml.DblType(),
    "Antenna/AntPattern/GainBSPoly": ssxml.PolyType(),
    "Antenna/AntPattern/AntPolRef/AmpX": ssxml.DblType(),
    "Antenna/AntPattern/AntPolRef/AmpY": ssxml.DblType(),
    "Antenna/AntPattern/AntPolRef/PhaseX": ssxml.DblType(),
    "Antenna/AntPattern/AntPolRef/PhaseY": ssxml.DblType(),
}
TRANSCODERS |= {
    "ErrorParameters/SARImage/Monostatic/PosVelError/Frame": ssxml.TxtType(),
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
    "ErrorParameters/SARImage/Bistatic/PosVelError/TxFrame": ssxml.TxtType(),
    "ErrorParameters/SARImage/Bistatic/PosVelError/TxPVCov": MtxType((6, 6)),
    "ErrorParameters/SARImage/Bistatic/PosVelError/RcvFrame": ssxml.TxtType(),
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
        f"ErrorParameters/{d}Sensor/PosVelError/Frame": ssxml.TxtType(),
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
    "GeoInfo/Desc": ssxml.ParameterType(),
    "GeoInfo/Point": ssxml.LatLonType(),
    "GeoInfo/Line": ssxml.ListType("Endpoint", ssxml.LatLonType()),
    "GeoInfo/Polygon": ssxml.ListType("Vertex", ssxml.LatLonType()),
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
    XmlHelper for Compensated Radar Signal Data (CRSD).

    """

    _transcoders_ = TRANSCODERS

    def _get_simple_path(self, elem):
        return re.sub(r"(GeoInfo/)+", "GeoInfo/", super()._get_simple_path(elem))
