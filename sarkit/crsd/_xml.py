"""
Functions for interacting with CRSD XML
"""

import re

import sarkit._xmlhelp as skxml
import sarkit.cphd as skcphd


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
class XdtType(skxml.XdtType):
    pass


@skxml.inheritdocstring
class IntType(skxml.IntType):
    pass


@skxml.inheritdocstring
class DblType(skxml.DblType):
    pass


@skxml.inheritdocstring
class HexType(skxml.HexType):
    pass


@skxml.inheritdocstring
class LineSampType(skxml.LineSampType):
    pass


@skxml.inheritdocstring
class XyType(skxml.XyType):
    pass


@skxml.inheritdocstring
class XyzType(skxml.XyzType):
    pass


@skxml.inheritdocstring
class LatLonType(skxml.LatLonType):
    pass


@skxml.inheritdocstring
class LatLonHaeType(skxml.LatLonHaeType):
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


# PxP/APxP are below


@skxml.inheritdocstring
class MtxType(skxml.MtxType):
    pass


@skxml.inheritdocstring
class ParameterType(skxml.ParameterType):
    pass


# The following transcoders happen to share common implementations with CPHD
class PxpType(skcphd.PvpType):
    """Transcoder for Per-x-Parameter (PxP) XML parameter types."""


class AddedPxpType(skcphd.AddedPvpType):
    """Transcoder for Added Per-x-Parameter (APxP) XML parameter types."""


@skxml.inheritdocstring
class ImageAreaCornerPointsType(skcphd.ImageAreaCornerPointsType):
    pass


class EdfType(skxml.SequenceType):
    """
    Transcoder for Error Decorrelation Function (EDF) XML parameter types.

    """

    def __init__(self) -> None:
        super().__init__(
            subelements={c: skxml.DblType() for c in ("CorrCoefZero", "DecorrRate")}
        )

    def parse_elem(self, elem) -> tuple[float, float]:
        """Returns (CorrCoefZero, DecorrRate) values encoded in ``elem``."""
        return tuple(super().parse_subelements(elem).values())

    def set_elem(self, elem, val: tuple[float, float]) -> None:
        """Set children of ``elem`` from tuple: (``CorrCoefZero``, ``DecorrRate``)."""
        super().set_subelements(elem, {"CorrCoefZero": val[0], "DecorrRate": val[1]})


TRANSCODERS: dict[str, skxml.Type] = {
    "ProductInfo/ProductName": TxtType(),
    "ProductInfo/Classification": TxtType(),
    "ProductInfo/ReleaseInfo": TxtType(),
    "ProductInfo/CountryCode": TxtType(),
    "ProductInfo/Profile": TxtType(),
    "ProductInfo/CreationInfo/Application": TxtType(),
    "ProductInfo/CreationInfo/DateTime": XdtType(),
    "ProductInfo/CreationInfo/Site": TxtType(),
    "ProductInfo/CreationInfo/Parameter": ParameterType(),
    "ProductInfo/Parameter": ParameterType(),
}
TRANSCODERS |= {
    "SARInfo/CollectType": TxtType(),
    "SARInfo/RadarMode/ModeType": TxtType(),
    "SARInfo/RadarMode/ModeID": TxtType(),
    "SARInfo/Parameter": ParameterType(),
}
TRANSCODERS |= {
    "TransmitInfo/SensorName": TxtType(),
    "TransmitInfo/EventName": TxtType(),
    "TransmitInfo/Parameter": ParameterType(),
}
TRANSCODERS |= {
    "ReceiveInfo/SensorName": TxtType(),
    "ReceiveInfo/EventName": TxtType(),
    "ReceiveInfo/Parameter": ParameterType(),
}
TRANSCODERS |= {
    "Global/CollectionRefTime": XdtType(),
    "Global/TropoParameters/N0": DblType(),
    "Global/TropoParameters/RefHeight": TxtType(),
    "Global/TropoParameters/N0ErrorStdDev": DblType(),
    "Global/IonoParameters/TECV": DblType(),
    "Global/IonoParameters/F2Height": DblType(),
    "Global/IonoParameters/TECVErrorStdDev": DblType(),
    "Global/Transmit/TxTime1": DblType(),
    "Global/Transmit/TxTime2": DblType(),
    "Global/Transmit/FxMin": DblType(),
    "Global/Transmit/FxMax": DblType(),
    "Global/Receive/RcvStartTime1": DblType(),
    "Global/Receive/RcvStartTime2": DblType(),
    "Global/Receive/FrcvMin": DblType(),
    "Global/Receive/FrcvMax": DblType(),
}
TRANSCODERS |= {
    "SceneCoordinates/EarthModel": TxtType(),
    "SceneCoordinates/IARP/ECF": XyzType(),
    "SceneCoordinates/IARP/LLH": LatLonHaeType(),
    "SceneCoordinates/ReferenceSurface/Planar/uIAX": XyzType(),
    "SceneCoordinates/ReferenceSurface/Planar/uIAY": XyzType(),
    "SceneCoordinates/ReferenceSurface/HAE/uIAXLL": LatLonType(),
    "SceneCoordinates/ReferenceSurface/HAE/uIAYLL": LatLonType(),
    "SceneCoordinates/ImageArea/X1Y1": XyType(),
    "SceneCoordinates/ImageArea/X2Y2": XyType(),
    "SceneCoordinates/ImageArea/Polygon": skxml.ListType("Vertex", XyType()),
    "SceneCoordinates/ImageAreaCornerPoints": ImageAreaCornerPointsType(),
    "SceneCoordinates/ExtendedArea/X1Y1": XyType(),
    "SceneCoordinates/ExtendedArea/X2Y2": XyType(),
    "SceneCoordinates/ExtendedArea/Polygon": skxml.ListType("Vertex", XyType()),
    "SceneCoordinates/ImageGrid/Identifier": TxtType(),
    "SceneCoordinates/ImageGrid/IARPLocation": LineSampType(),
    "SceneCoordinates/ImageGrid/IAXExtent/LineSpacing": DblType(),
    "SceneCoordinates/ImageGrid/IAXExtent/FirstLine": IntType(),
    "SceneCoordinates/ImageGrid/IAXExtent/NumLines": IntType(),
    "SceneCoordinates/ImageGrid/IAYExtent/SampleSpacing": DblType(),
    "SceneCoordinates/ImageGrid/IAYExtent/FirstSample": IntType(),
    "SceneCoordinates/ImageGrid/IAYExtent/NumSamples": IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/NumSegments": IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/Identifier": TxtType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/StartLine": IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/StartSample": IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/EndLine": IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/EndSample": IntType(),
    "SceneCoordinates/ImageGrid/SegmentList/Segment/SegmentPolygon": skxml.ListType(
        "SV", LineSampType()
    ),
}
TRANSCODERS |= {
    "Data/Support/NumSupportArrays": IntType(),
    "Data/Support/SupportArray/SAId": TxtType(),
    "Data/Support/SupportArray/NumRows": IntType(),
    "Data/Support/SupportArray/NumCols": IntType(),
    "Data/Support/SupportArray/BytesPerElement": IntType(),
    "Data/Support/SupportArray/ArrayByteOffset": IntType(),
    "Data/Transmit/NumBytesPPP": IntType(),
    "Data/Transmit/NumTxSequences": IntType(),
    "Data/Transmit/TxSequence/TxId": TxtType(),
    "Data/Transmit/TxSequence/NumPulses": IntType(),
    "Data/Transmit/TxSequence/PPPArrayByteOffset": IntType(),
    "Data/Receive/SignalArrayFormat": TxtType(),
    "Data/Receive/NumBytesPVP": IntType(),
    "Data/Receive/NumCRSDChannels": IntType(),
    "Data/Receive/SignalCompression/Identifier": TxtType(),
    "Data/Receive/SignalCompression/CompressedSignalSize": IntType(),
    "Data/Receive/SignalCompression/Processing/Type": TxtType(),
    "Data/Receive/SignalCompression/Processing/Parameter": ParameterType(),
    "Data/Receive/Channel/ChId": TxtType(),
    "Data/Receive/Channel/NumVectors": IntType(),
    "Data/Receive/Channel/NumSamples": IntType(),
    "Data/Receive/Channel/SignalArrayByteOffset": IntType(),
    "Data/Receive/Channel/PVPArrayByteOffset": IntType(),
}
TRANSCODERS |= {
    "TxSequence/RefTxId": TxtType(),
    "TxSequence/TxWFType": TxtType(),
    "TxSequence/Parameters/Identifier": TxtType(),
    "TxSequence/Parameters/RefPulseIndex": IntType(),
    "TxSequence/Parameters/XMId": TxtType(),
    "TxSequence/Parameters/FxResponseId": TxtType(),
    "TxSequence/Parameters/FxBWFixed": BoolType(),
    "TxSequence/Parameters/FxC": DblType(),
    "TxSequence/Parameters/FxBW": DblType(),
    "TxSequence/Parameters/TXmtMin": DblType(),
    "TxSequence/Parameters/TXmtMax": DblType(),
    "TxSequence/Parameters/TxTime1": DblType(),
    "TxSequence/Parameters/TxTime2": DblType(),
    "TxSequence/Parameters/TxAPCId": TxtType(),
    "TxSequence/Parameters/TxAPATId": TxtType(),
    "TxSequence/Parameters/TxRefPoint/ECF": XyzType(),
    "TxSequence/Parameters/TxRefPoint/IAC": XyType(),
    "TxSequence/Parameters/TxPolarization/PolarizationID": TxtType(),
    "TxSequence/Parameters/TxPolarization/AmpH": DblType(),
    "TxSequence/Parameters/TxPolarization/AmpV": DblType(),
    "TxSequence/Parameters/TxPolarization/PhaseH": DblType(),
    "TxSequence/Parameters/TxPolarization/PhaseV": DblType(),
    "TxSequence/Parameters/TxRefRadIntensity": DblType(),
    "TxSequence/Parameters/TxRadIntErrorStdDev": DblType(),
    "TxSequence/Parameters/TxRefLAtm": DblType(),
    "TxSequence/Parameters/Parameter": ParameterType(),
}
TRANSCODERS |= {
    "Channel/RefChId": TxtType(),
    "Channel/Parameters/Identifier": TxtType(),
    "Channel/Parameters/RefVectorIndex": IntType(),
    "Channel/Parameters/RefFreqFixed": BoolType(),
    "Channel/Parameters/FrcvFixed": BoolType(),
    "Channel/Parameters/SignalNormal": BoolType(),
    "Channel/Parameters/F0Ref": DblType(),
    "Channel/Parameters/Fs": DblType(),
    "Channel/Parameters/BWInst": DblType(),
    "Channel/Parameters/RcvStartTime1": DblType(),
    "Channel/Parameters/RcvStartTime2": DblType(),
    "Channel/Parameters/FrcvMin": DblType(),
    "Channel/Parameters/FrcvMax": DblType(),
    "Channel/Parameters/RcvAPCId": TxtType(),
    "Channel/Parameters/RcvAPATId": TxtType(),
    "Channel/Parameters/RcvRefPoint/ECF": XyzType(),
    "Channel/Parameters/RcvRefPoint/IAC": XyType(),
    "Channel/Parameters/RcvPolarization/PolarizationID": TxtType(),
    "Channel/Parameters/RcvPolarization/AmpH": DblType(),
    "Channel/Parameters/RcvPolarization/AmpV": DblType(),
    "Channel/Parameters/RcvPolarization/PhaseH": DblType(),
    "Channel/Parameters/RcvPolarization/PhaseV": DblType(),
    "Channel/Parameters/RcvRefIrradiance": DblType(),
    "Channel/Parameters/RcvIrradianceErrorStdDev": DblType(),
    "Channel/Parameters/RcvRefLAtm": DblType(),
    "Channel/Parameters/PNCRSD": DblType(),
    "Channel/Parameters/BNCRSD": DblType(),
    "Channel/Parameters/Parameter": ParameterType(),
    "Channel/Parameters/SARImage/TxId": TxtType(),
    "Channel/Parameters/SARImage/RefVectorPulseIndex": IntType(),
    "Channel/Parameters/SARImage/TxPolarization/PolarizationID": TxtType(),
    "Channel/Parameters/SARImage/TxPolarization/AmpH": DblType(),
    "Channel/Parameters/SARImage/TxPolarization/AmpV": DblType(),
    "Channel/Parameters/SARImage/TxPolarization/PhaseH": DblType(),
    "Channel/Parameters/SARImage/TxPolarization/PhaseV": DblType(),
    "Channel/Parameters/SARImage/DwellTimes/Polynomials/CODId": TxtType(),
    "Channel/Parameters/SARImage/DwellTimes/Polynomials/DwellId": TxtType(),
    "Channel/Parameters/SARImage/DwellTimes/Array/DTAId": TxtType(),
    "Channel/Parameters/SARImage/ImageArea/X1Y1": XyType(),
    "Channel/Parameters/SARImage/ImageArea/X2Y2": XyType(),
    "Channel/Parameters/SARImage/ImageArea/Polygon": skxml.ListType("Vertex", XyType()),
}
TRANSCODERS |= {
    "ReferenceGeometry/RefPoint/ECF": XyzType(),
    "ReferenceGeometry/RefPoint/IAC": XyType(),
    "ReferenceGeometry/SARImage/CODTime": DblType(),
    "ReferenceGeometry/SARImage/DwellTime": DblType(),
    "ReferenceGeometry/SARImage/ReferenceTime": DblType(),
    "ReferenceGeometry/SARImage/ARPPos": XyzType(),
    "ReferenceGeometry/SARImage/ARPVel": XyzType(),
    "ReferenceGeometry/SARImage/BistaticAngle": DblType(),
    "ReferenceGeometry/SARImage/BistaticAngleRate": DblType(),
    "ReferenceGeometry/SARImage/SideOfTrack": TxtType(),
    "ReferenceGeometry/SARImage/SlantRange": DblType(),
    "ReferenceGeometry/SARImage/GroundRange": DblType(),
    "ReferenceGeometry/SARImage/DopplerConeAngle": DblType(),
    "ReferenceGeometry/SARImage/SquintAngle": DblType(),
    "ReferenceGeometry/SARImage/AzimuthAngle": DblType(),
    "ReferenceGeometry/SARImage/GrazeAngle": DblType(),
    "ReferenceGeometry/SARImage/IncidenceAngle": DblType(),
    "ReferenceGeometry/SARImage/TwistAngle": DblType(),
    "ReferenceGeometry/SARImage/SlopeAngle": DblType(),
    "ReferenceGeometry/SARImage/LayoverAngle": DblType(),
}
for d in ("Tx", "Rcv"):
    TRANSCODERS |= {
        f"ReferenceGeometry/{d}Parameters/Time": DblType(),
        f"ReferenceGeometry/{d}Parameters/APCPos": XyzType(),
        f"ReferenceGeometry/{d}Parameters/APCVel": XyzType(),
        f"ReferenceGeometry/{d}Parameters/SideOfTrack": TxtType(),
        f"ReferenceGeometry/{d}Parameters/SlantRange": DblType(),
        f"ReferenceGeometry/{d}Parameters/GroundRange": DblType(),
        f"ReferenceGeometry/{d}Parameters/DopplerConeAngle": DblType(),
        f"ReferenceGeometry/{d}Parameters/SquintAngle": DblType(),
        f"ReferenceGeometry/{d}Parameters/AzimuthAngle": DblType(),
        f"ReferenceGeometry/{d}Parameters/GrazeAngle": DblType(),
        f"ReferenceGeometry/{d}Parameters/IncidenceAngle": DblType(),
    }
TRANSCODERS |= {
    "DwellPolynomials/NumCODTimes": IntType(),
    "DwellPolynomials/CODTime/Identifier": TxtType(),
    "DwellPolynomials/CODTime/CODTimePoly": Poly2dType(),
    "DwellPolynomials/NumDwellTimes": IntType(),
    "DwellPolynomials/DwellTime/Identifier": TxtType(),
    "DwellPolynomials/DwellTime/DwellTimePoly": Poly2dType(),
}
TRANSCODERS |= {
    "SupportArray/GainPhaseArray/Identifier": TxtType(),
    "SupportArray/GainPhaseArray/ElementFormat": TxtType(),
    "SupportArray/GainPhaseArray/X0": DblType(),
    "SupportArray/GainPhaseArray/Y0": DblType(),
    "SupportArray/GainPhaseArray/XSS": DblType(),
    "SupportArray/GainPhaseArray/YSS": DblType(),
    "SupportArray/GainPhaseArray/NODATA": HexType(),
    "SupportArray/FxResponseArray/Identifier": TxtType(),
    "SupportArray/FxResponseArray/ElementFormat": TxtType(),
    "SupportArray/FxResponseArray/Fx0FXR": DblType(),
    "SupportArray/FxResponseArray/FxSSFXR": DblType(),
    "SupportArray/XMArray/Identifier": TxtType(),
    "SupportArray/XMArray/ElementFormat": TxtType(),
    "SupportArray/XMArray/TsXMA": DblType(),
    "SupportArray/XMArray/MaxXMBW": DblType(),
    "SupportArray/DwellTimeArray/Identifier": TxtType(),
    "SupportArray/DwellTimeArray/ElementFormat": TxtType(),
    "SupportArray/DwellTimeArray/X0": DblType(),
    "SupportArray/DwellTimeArray/Y0": DblType(),
    "SupportArray/DwellTimeArray/XSS": DblType(),
    "SupportArray/DwellTimeArray/YSS": DblType(),
    "SupportArray/DwellTimeArray/NODATA": HexType(),
    "SupportArray/IAZArray/Identifier": TxtType(),
    "SupportArray/IAZArray/ElementFormat": TxtType(),
    "SupportArray/IAZArray/X0": DblType(),
    "SupportArray/IAZArray/Y0": DblType(),
    "SupportArray/IAZArray/XSS": DblType(),
    "SupportArray/IAZArray/YSS": DblType(),
    "SupportArray/IAZArray/NODATA": HexType(),
    "SupportArray/AddedSupportArray/Identifier": TxtType(),
    "SupportArray/AddedSupportArray/ElementFormat": TxtType(),
    "SupportArray/AddedSupportArray/X0": DblType(),
    "SupportArray/AddedSupportArray/Y0": DblType(),
    "SupportArray/AddedSupportArray/XSS": DblType(),
    "SupportArray/AddedSupportArray/YSS": DblType(),
    "SupportArray/AddedSupportArray/NODATA": HexType(),
    "SupportArray/AddedSupportArray/XUnits": TxtType(),
    "SupportArray/AddedSupportArray/YUnits": TxtType(),
    "SupportArray/AddedSupportArray/ZUnits": TxtType(),
    "SupportArray/AddedSupportArray/Parameter": ParameterType(),
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
    "Antenna/NumACFs": IntType(),
    "Antenna/NumAPCs": IntType(),
    "Antenna/NumAPATs": IntType(),
    "Antenna/AntCoordFrame/Identifier": TxtType(),
    "Antenna/AntPhaseCenter/Identifier": TxtType(),
    "Antenna/AntPhaseCenter/ACFId": TxtType(),
    "Antenna/AntPhaseCenter/APCXYZ": XyzType(),
    "Antenna/AntPattern/Identifier": TxtType(),
    "Antenna/AntPattern/FreqZero": DblType(),
    "Antenna/AntPattern/ArrayGPId": TxtType(),
    "Antenna/AntPattern/ElemGPId": TxtType(),
    "Antenna/AntPattern/EBFreqShift/DCXSF": DblType(),
    "Antenna/AntPattern/EBFreqShift/DCYSF": DblType(),
    "Antenna/AntPattern/MLFreqDilation/DCXSF": DblType(),
    "Antenna/AntPattern/MLFreqDilation/DCYSF": DblType(),
    "Antenna/AntPattern/GainBSPoly": PolyType(),
    "Antenna/AntPattern/AntPolRef/AmpX": DblType(),
    "Antenna/AntPattern/AntPolRef/AmpY": DblType(),
    "Antenna/AntPattern/AntPolRef/PhaseX": DblType(),
    "Antenna/AntPattern/AntPolRef/PhaseY": DblType(),
}
TRANSCODERS |= {
    "ErrorParameters/SARImage/Monostatic/PosVelError/Frame": TxtType(),
    "ErrorParameters/SARImage/Monostatic/PosVelError/PVCov": MtxType((6, 6)),
    "ErrorParameters/SARImage/Monostatic/PosVelError/PosDecorr": EdfType(),
    "ErrorParameters/SARImage/Monostatic/RadarSensor/TimeFreqCov": MtxType((3, 3)),
    "ErrorParameters/SARImage/Monostatic/RadarSensor/TimeFreqDecorr/TxTimeDecorr": EdfType(),
    "ErrorParameters/SARImage/Monostatic/RadarSensor/TimeFreqDecorr/RcvTimeDecorr": EdfType(),
    "ErrorParameters/SARImage/Monostatic/RadarSensor/TimeFreqDecorr/ClockFreqDecorr": EdfType(),
    "ErrorParameters/SARImage/Bistatic/PosVelError/TxFrame": TxtType(),
    "ErrorParameters/SARImage/Bistatic/PosVelError/TxPVCov": MtxType((6, 6)),
    "ErrorParameters/SARImage/Bistatic/PosVelError/RcvFrame": TxtType(),
    "ErrorParameters/SARImage/Bistatic/PosVelError/RcvPVCov": MtxType((6, 6)),
    "ErrorParameters/SARImage/Bistatic/PosVelError/TxRcvPVCov": MtxType((6, 6)),
    "ErrorParameters/SARImage/Bistatic/PosVelError/PosVelDecorr/TxPosDecorr": EdfType(),
    "ErrorParameters/SARImage/Bistatic/PosVelError/PosVelDecorr/RcvPosDecorr": EdfType(),
    "ErrorParameters/SARImage/Bistatic/RadarSensor/TimeFreqCov": MtxType((4, 4)),
    "ErrorParameters/SARImage/Bistatic/RadarSensor/TimeFreqDecorr/TxTimeDecorr": EdfType(),
    "ErrorParameters/SARImage/Bistatic/RadarSensor/TimeFreqDecorr/RcvTimeDecorr": EdfType(),
    "ErrorParameters/SARImage/Bistatic/RadarSensor/TimeFreqDecorr/TxClockFreqDecorr": EdfType(),
    "ErrorParameters/SARImage/Bistatic/RadarSensor/TimeFreqDecorr/RcvClockFreqDecorr": EdfType(),
}
for d in ("Tx", "Rcv"):
    TRANSCODERS |= {
        f"ErrorParameters/{d}Sensor/PosVelError/Frame": TxtType(),
        f"ErrorParameters/{d}Sensor/PosVelError/PVCov": MtxType((6, 6)),
        f"ErrorParameters/{d}Sensor/PosVelError/PosDecorr": EdfType(),
        f"ErrorParameters/{d}Sensor/RadarSensor/TimeFreqCov": MtxType((2, 2)),
        f"ErrorParameters/{d}Sensor/RadarSensor/TimeFreqDecorr/TimeDecorr": EdfType(),
        f"ErrorParameters/{d}Sensor/RadarSensor/TimeFreqDecorr/ClockFreqDecorr": EdfType(),
    }
TRANSCODERS |= {
    "GeoInfo/Desc": ParameterType(),
    "GeoInfo/Point": LatLonType(),
    "GeoInfo/Line": skxml.ListType("Endpoint", LatLonType()),
    "GeoInfo/Polygon": skxml.ListType("Vertex", LatLonType()),
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
