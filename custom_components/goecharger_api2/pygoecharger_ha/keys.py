import logging
from enum import Enum
from typing import (
    NamedTuple, Final
)

# from aenum import Enum, extend_enum

_LOGGER: logging.Logger = logging.getLogger(__package__)

IS_TRIGGER: Final = "TRIGGER"

class CAT(Enum):
    CONFIG = "CONF"
    STATUS = "STAT"
    OTHER = "OTHE"
    CONSTANT = "CONS"


class ApiKey(NamedTuple):
    key: str
    cat: str
    writeable: bool = False
    writeonly: bool = False

# see https://github.com/goecharger/go-eCharger-API-v2/blob/main/apikeys-en.md for details
class Tag(ApiKey, Enum):

    def __hash__(self) -> int:
        return hash(self.key)

    def __str__(self):
        return self.key

    # allowChargePause (car compatiblity)
    ACP = ApiKey(key="acp", cat=CAT.CONFIG, writeable=True)
    # access_control user setting (Open=0, Wait=1)
    ACS = ApiKey(key="acs", cat=CAT.CONFIG, writeable=True)
    # Mit wie vielen Ampere darf das Auto derzeit laden?
    ACU = ApiKey(key="acu", cat=CAT.STATUS)
    # Wird der 16A Adapter benutzt? Limitiert den Ladestrom auf 16A
    ADI = ApiKey(key="adi", cat=CAT.STATUS)
    # Darf das Auto derzeit laden?
    ALW = ApiKey(key="alw", cat=CAT.STATUS)
    # ampere_max limit
    AMA = ApiKey(key="ama", cat=CAT.CONFIG, writeable=True)
    # requestedCurrent in Ampere, used for display on LED ring and logic calculations
    AMP = ApiKey(key="amp", cat=CAT.CONFIG, writeable=True)
    # temperatureCurrentLimit
    AMT = ApiKey(key="amt", cat=CAT.STATUS)
    # automatic stop remain in aWATTar
    ARA = ApiKey(key="ara", cat=CAT.CONFIG, writeable=True)
    # automatic stop energy in Wh
    ATE = ApiKey(key="ate", cat=CAT.CONFIG, writeable=True)
    # nextTripPlanData (debug)
    ATP = ApiKey(key="atp", cat=CAT.STATUS)
    # automatic stop time in seconds since day begin, calculation: (hours3600)+(minutes60)+(seconds)
    ATT = ApiKey(key="att", cat=CAT.CONFIG, writeable=True)
    # awattar country (Austria=0, Germany=1)
    AWC = ApiKey(key="awc", cat=CAT.CONFIG, writeable=True)
    # awattar current price
    AWCP = ApiKey(key="awcp", cat=CAT.STATUS)
    # useAwattar
    AWE = ApiKey(key="awe", cat=CAT.CONFIG, writeable=True)
    # awattarMaxPrice in ct
    AWP = ApiKey(key="awp", cat=CAT.CONFIG, writeable=True)
    # Button allow Current change (0=AlwaysLock, 1=LockWhenCarIsConnected, 2=LockWhenCarIsCharging, 3=NeverLock)
    BAC = ApiKey(key="bac", cat=CAT.CONFIG, writeable=True)
    # carState, null if internal error (Unknown/Error=0, Idle=1, Charging=2, WaitCar=3, Complete=4, Error=5)
    CAR = ApiKey(key="car", cat=CAT.STATUS)
    # 
    CARDS = ApiKey(key="cards", cat=CAT.CONFIG, writeable=True)
    # cable_current_limit in A
    CBL = ApiKey(key="cbl", cat=CAT.STATUS)
    # car consumption (only stored for app)
    CCO = ApiKey(key="cco", cat=CAT.CONFIG)
    # chargectrl recommended version
    CCRV = ApiKey(key="ccrv", cat=CAT.CONSTANT)
    # charge controller update progress (null if no update is in progress)
    CCU = ApiKey(key="ccu", cat=CAT.STATUS)
    # Currently connected WiFi
    CCW = ApiKey(key="ccw", cat=CAT.STATUS)
    # charging duration info (null=no charging in progress, type=0 counter going up, type=1 duration in ms)
    CDI = ApiKey(key="cdi", cat=CAT.STATUS)

    # cll | R | TYPE | Status | Current limits list
    # "cll": {
    #     "accessControl": 0,
    #     "currentLimitMax": 22,
    #     "minChargingCurrent": 6,
    #     "requestedCurrent": 6,
    #     "temperatureCurrentLimit": 32,
    #     "unsymetryCurrentLimit": 32
    # },
    CLL = ApiKey(key="cll", cat=CAT.STATUS)

    # current limit presets, max. 5 entries
    CLP = ApiKey(key="clp", cat=CAT.CONFIG, writeable=True)
    # Cable unlock status (Unknown=0, Unlocked=1, UnlockFailed=2, Locked=3, LockFailed=4, LockUnlockPowerout=5)
    CUS = ApiKey(key="cus", cat=CAT.STATUS)
    # cloud websocket enabled"
    CWE = ApiKey(key="cwe", cat=CAT.CONFIG, writeable=True)
    # set this to 0-9 to clear card (erases card name, energy and rfid id)
    DEL = ApiKey(key="del", cat=CAT.OTHER, writeable=True, writeonly=True)
    # deltaA
    DELTAA = ApiKey(key="deltaa", cat=CAT.STATUS)
    # deltaP
    DELTAP = ApiKey(key="deltap", cat=CAT.STATUS)
    # set this to 0-9 to delete sta config (erases ssid, key, ...)
    DELW = ApiKey(key="delw", cat=CAT.OTHER, writeable=True, writeonly=True)
    # DNS server
    DNS = ApiKey(key="dns", cat=CAT.STATUS)
    # Lade Energy Limit, gemessen in Wh, null bedeutet deaktiviert, nicht mit der Next-Trip Energie zu verwechseln
    DWO = ApiKey(key="dwo", cat=CAT.CONFIG, writeable=True)
    # error, null if internal error (None = 0, FiAc = 1, FiDc = 2, Phase = 3, Overvolt = 4, Overamp = 5, Diode = 6, PpInvalid = 7, GndInvalid = 8, ContactorStuck = 9, ContactorMiss = 10, FiUnknown = 11, Unknown = 12, Overtemp = 13, NoComm = 14, StatusLockStuckOpen = 15, StatusLockStuckLocked = 16, Reserved20 = 20, Reserved21 = 21, Reserved22 = 22, Reserved23 = 23, Reserved24 = 24)
    ERR = ApiKey(key="err", cat=CAT.STATUS)
    # energy set kwh (only stored for app)
    ESK = ApiKey(key="esk", cat=CAT.CONFIG)
    # energy_total, measured in Wh
    ETO = ApiKey(key="eto", cat=CAT.STATUS)
    # effectiveRoundingMode
    FERM = ApiKey(key="ferm", cat=CAT.STATUS)
    # lock feedback (NoProblem=0, ProblemLock=1, ProblemUnlock=2)
    FFB = ApiKey(key="ffb", cat=CAT.STATUS)
    # Stromnetz frequency (~50Hz) or 0 if unknown
    FHZ = ApiKey(key="fhz", cat=CAT.STATUS)
    # minChargeTime in milliseconds
    FMT = ApiKey(key="fmt", cat=CAT.CONFIG, writeable=True)
    # friendlyName
    FNA = ApiKey(key="fna", cat=CAT.CONFIG, writeable=True)
    # forceState (Neutral=0, Off=1, On=2)
    FRC = ApiKey(key="frc", cat=CAT.CONFIG, writeable=True)
    # roundingMode PreferPowerFromGrid=0, Default=1, PreferPowerToGrid=2
    FRM = ApiKey(key="frm", cat=CAT.CONFIG)
    # force_single_phase, this is only the result of the charging logic, if it wishes single force or not at the moment
    FSP = ApiKey(key="fsp", cat=CAT.STATUS)
    # force single phase toggle wished since
    FSPTWS = ApiKey(key="fsptws", cat=CAT.STATUS)
    # startingPower in watts
    FST = ApiKey(key="fst", cat=CAT.CONFIG, writeable=True)
    # usePvSurplus
    FUP = ApiKey(key="fup", cat=CAT.CONFIG, writeable=True)
    # firmware from CarControl
    FWC = ApiKey(key="fwc", cat=CAT.CONSTANT)
    # FW_VERSION
    FWV = ApiKey(key="fwv", cat=CAT.CONSTANT)
    # zeroFeedin
    FZF = ApiKey(key="fzf", cat=CAT.CONFIG, writeable=True)
    # hostname used on STA interface
    HOST = ApiKey(key="host", cat=CAT.STATUS)
    # httpStaAuthentication
    HSA = ApiKey(key="hsa", cat=CAT.CONFIG, writeable=True)
    # Inverter data override
    IDO = ApiKey(key="ido", cat=CAT.CONFIG)
    # age of inverter data
    INVA = ApiKey(key="inva", cat=CAT.STATUS)
    # lastButtonPress in milliseconds
    LBP = ApiKey(key="lbp", cat=CAT.STATUS)
    # led_bright, 0-255
    LBR = ApiKey(key="lbr", cat=CAT.CONFIG, writeable=True)
    # lastCarStateChangedFromCharging (in ms)
    LCCFC = ApiKey(key="lccfc", cat=CAT.STATUS)
    # lastCarStateChangedFromIdle (in ms)
    LCCFI = ApiKey(key="lccfi", cat=CAT.STATUS)
    # lastCarStateChangedToCharging (in ms)
    LCCTC = ApiKey(key="lcctc", cat=CAT.STATUS)
    # Effective lock setting, as sent to Charge Ctrl (Normal=0, AutoUnlock=1, AlwaysLock=2, ForceUnlock=3)
    LCK = ApiKey(key="lck", cat=CAT.STATUS)
    # [NOT-USED by Integration] internal infos about currently running led animation
    # LED = ApiKey(key="led", cat=CAT.STATUS)
    # last force single phase toggle
    LFSPT = ApiKey(key="lfspt", cat=CAT.STATUS)
    # logic mode (Default=3, Awattar=4, AutomaticStop=5)
    LMO = ApiKey(key="lmo", cat=CAT.CONFIG, writeable=True)
    # last model status change
    LMSC = ApiKey(key="lmsc", cat=CAT.STATUS)
    # load balancing ampere
    LOA = ApiKey(key="loa", cat=CAT.STATUS)
    # local time
    LOC = ApiKey(key="loc", cat=CAT.STATUS)
    # Load balancing enabled
    LOE = ApiKey(key="loe", cat=CAT.CONFIG, writeable=True)
    # load_fallback
    LOF = ApiKey(key="lof", cat=CAT.CONFIG, writeable=True)
    # load_group_id
    LOG = ApiKey(key="log", cat=CAT.CONFIG, writeable=True)
    # load_priority
    LOP = ApiKey(key="lop", cat=CAT.CONFIG, writeable=True)
    # load balancing total amp
    LOT = ApiKey(key="lot", cat=CAT.CONFIG, writeable=True)
    # load balancing type (Static=0, Dynamic=1)
    LOTY = ApiKey(key="loty", cat=CAT.CONFIG, writeable=True)
    # last pv surplus calculation
    LPSC = ApiKey(key="lpsc", cat=CAT.STATUS)
    # set this to 0-9 to learn last read card id
    LRN = ApiKey(key="lrn", cat=CAT.OTHER, writeable=True, writeonly=True)
    # led_save_energy
    LSE = ApiKey(key="lse", cat=CAT.CONFIG, writeable=True)
    # load_mapping (uint8_t[3])
    MAP = ApiKey(key="map", cat=CAT.CONFIG, writeable=True)
    # minChargingCurrent
    MCA = ApiKey(key="mca", cat=CAT.CONFIG, writeable=True)
    # minimumChargingInterval in milliseconds (0 means disabled)
    MCI = ApiKey(key="mci", cat=CAT.CONFIG, writeable=True)
    # minChargePauseDuration in milliseconds (0 means disabled)
    MCPD = ApiKey(key="mcpd", cat=CAT.CONFIG, writeable=True)
    # minChargePauseEndsAt (set to null to abort current minChargePauseDuration)
    MCPEA = ApiKey(key="mcpea", cat=CAT.STATUS, writeable=True)
    # maximumMeasuredChargingPower (debug)
    MMP = ApiKey(key="mmp", cat=CAT.STATUS)
    # Reason why we allow charging or not right now (NotChargingBecauseNoChargeCtrlData=0, NotChargingBecauseOvertemperature=1, NotChargingBecauseAccessControlWait=2, ChargingBecauseForceStateOn=3, NotChargingBecauseForceStateOff=4, NotChargingBecauseScheduler=5, NotChargingBecauseEnergyLimit=6, ChargingBecauseAwattarPriceLow=7, ChargingBecauseAutomaticStopTestLadung=8, ChargingBecauseAutomaticStopNotEnoughTime=9, ChargingBecauseAutomaticStop=10, ChargingBecauseAutomaticStopNoClock=11, ChargingBecausePvSurplus=12, ChargingBecauseFallbackGoEDefault=13, ChargingBecauseFallbackGoEScheduler=14, ChargingBecauseFallbackDefault=15, NotChargingBecauseFallbackGoEAwattar=16, NotChargingBecauseFallbackAwattar=17, NotChargingBecauseFallbackAutomaticStop=18, ChargingBecauseCarCompatibilityKeepAlive=19, ChargingBecauseChargePauseNotAllowed=20, NotChargingBecauseSimulateUnplugging=22, NotChargingBecausePhaseSwitch=23, NotChargingBecauseMinPauseDuration=24)
    MODELSTATUS = ApiKey(key="modelStatus", cat=CAT.STATUS)
    # min phase toggle wait time (in milliseconds)
    MPTWT = ApiKey(key="mptwt", cat=CAT.CONFIG, writeable=True)
    # min phase wish switch time (in milliseconds)
    MPWST = ApiKey(key="mpwst", cat=CAT.CONFIG, writeable=True)
    # Default route
    NIF = ApiKey(key="nif", cat=CAT.STATUS)
    # norway_mode / ground check enabled when norway mode is disabled (inverted)
    NMO = ApiKey(key="nmo", cat=CAT.CONFIG, writeable=True)
    # energy array, U (L1, L2, L3, N), I (L1, L2, L3), P (L1, L2, L3, N, Total), pf (L1, L2, L3, N)
    NRG = ApiKey(key="nrg", cat=CAT.STATUS)

    # firmware update trigger (must specify a branch from ocu)
    OCT = ApiKey(key="oct", cat=CAT.OTHER, writeable=True, writeonly=True)
    # list of available firmware branches
    OCU = ApiKey(key="ocu", cat=CAT.STATUS)
    # OEM manufacturer
    OEM = ApiKey(key="oem", cat=CAT.CONSTANT)
    # pAkku in W
    PAKKU = ApiKey(key="pakku", cat=CAT.STATUS)
    # pGrid in W
    PGRID = ApiKey(key="pgrid", cat=CAT.STATUS)
    # pGridTarget in W
    PGT = ApiKey(key="pgt", cat=CAT.CONFIG, writeable=True)
    # phases
    PHA = ApiKey(key="pha", cat=CAT.STATUS)
    # numberOfPhases
    PNP = ApiKey(key="pnp", cat=CAT.STATUS)
    # prioOffset in W
    PO = ApiKey(key="po", cat=CAT.CONFIG, writeable=True)
    # pPv in W
    PPV = ApiKey(key="ppv", cat=CAT.STATUS)
    # phaseSwitchHysteresis in W
    PSH = ApiKey(key="psh", cat=CAT.CONFIG, writeable=True)
    # phaseSwitchMode (Auto=0, Force_1=1, Force_3=2)
    PSM = ApiKey(key="psm", cat=CAT.CONFIG, writeable=True)
    # forceSinglePhaseDuration (in milliseconds)
    PSMD = ApiKey(key="psmd", cat=CAT.CONFIG, writeable=True)
    # averagePAkku
    PVOPT_AVERAGEPAKKU = ApiKey(key="pvopt_averagePAkku", cat=CAT.STATUS)
    # averagePGrid
    PVOPT_AVERAGEPGRID = ApiKey(key="pvopt_averagePGrid", cat=CAT.STATUS)
    # averagePPv
    PVOPT_AVERAGEPPV = ApiKey(key="pvopt_averagePPv", cat=CAT.STATUS)
    # phase wish mode for debugging / only for pv optimizing / used for timers later (Force_3=0, Wish_1=1, Wish_3=2)
    PWM = ApiKey(key="pwm", cat=CAT.STATUS)
    # reboot_counter
    RBC = ApiKey(key="rbc", cat=CAT.STATUS)
    # time since boot in milliseconds
    RBT = ApiKey(key="rbt", cat=CAT.STATUS)
    # Relay Feedback
    RFB = ApiKey(key="rfb", cat=CAT.STATUS)
    # RSSI signal strength
    RSSI = ApiKey(key="rssi", cat=CAT.STATUS)
    # Ladestation neustarten
    RST = ApiKey(key="rst", cat=CAT.OTHER, writeable=True, writeonly=True)
    # wifi scan age
    SCAA = ApiKey(key="scaa", cat=CAT.STATUS)
    # wifi scan result (encryptionType: OPEN=0, WEP=1, WPA_PSK=2, WPA2_PSK=3, WPA_WPA2_PSK=4, WPA2_ENTERPRISE=5, WPA3_PSK=6, WPA2_WPA3_PSK=7)
    SCAN = ApiKey(key="scan", cat=CAT.STATUS)
    # scheduler_saturday, control enum values: Disabled=0, Inside=1, Outside=2
    SCH_SATUR = ApiKey(key="sch_satur", cat=CAT.CONFIG, writeable=True)
    # scheduler_sunday, control enum values: Disabled=0, Inside=1, Outside=2
    SCH_SUND = ApiKey(key="sch_sund", cat=CAT.CONFIG, writeable=True)
    # scheduler_weekday, control enum values: Disabled=0, Inside=1, Outside=2
    SCH_WEEK = ApiKey(key="sch_week", cat=CAT.CONFIG, writeable=True)
    # Button Allow Force change (0=AlwaysLock, 1=LockWhenCarIsConnected, 2=LockWhenCarIsCharging, 3=NeverLock)
    SDP = ApiKey(key="sdp", cat=CAT.CONFIG, writeable=True)
    # stopHysteresis in W
    SH = ApiKey(key="sh", cat=CAT.CONFIG, writeable=True)
    # threePhaseSwitchLevel
    SPL3 = ApiKey(key="spl3", cat=CAT.CONFIG, writeable=True)
    # serial number
    SSE = ApiKey(key="sse", cat=CAT.CONSTANT)
    # simulateUnpluggingShort
    SU = ApiKey(key="su", cat=CAT.CONFIG, writeable=True)
    # simulateUnpluggingAlways
    SUA = ApiKey(key="sua", cat=CAT.CONFIG, writeable=True)
    # simulate unpluging duration (in milliseconds)
    SUMD = ApiKey(key="sumd", cat=CAT.CONFIG, writeable=True)
    # timezone daylight saving mode, None=0, EuropeanSummerTime=1, UsDaylightTime=2
    TDS = ApiKey(key="tds", cat=CAT.CONFIG, writeable=True)
    # testLadungFinished (debug)
    TLF = ApiKey(key="tlf", cat=CAT.STATUS)
    # testLadungStarted (debug)
    TLS = ApiKey(key="tls", cat=CAT.STATUS)
    # temperature sensors
    TMA = ApiKey(key="tma", cat=CAT.STATUS)
    # timezone offset in minutes
    TOF = ApiKey(key="tof", cat=CAT.CONFIG, writeable=True)
    # 30 Sekunden Gesamtleistungsdurchschnitt (wird für genauere next-trip vorhersagen berechnet)
    TPA = ApiKey(key="tpa", cat=CAT.STATUS)
    # transaction, null when no transaction, 0 when without card, otherwise cardIndex + 1 (1: 0. card, 2: 1. card, ...)
    TRX = ApiKey(key="trx", cat=CAT.STATUS, writeable=True)
    # time server enabled (NTP)
    TSE = ApiKey(key="tse", cat=CAT.CONFIG, writeable=True)
    # time server sync status (RESET=0, COMPLETED=1, IN_PROGRESS=2)
    TSSS = ApiKey(key="tsss", cat=CAT.CONFIG)
    # Devicetype
    TYP = ApiKey(key="typ", cat=CAT.CONSTANT)
    # unlock_power_outage
    UPO = ApiKey(key="upo", cat=CAT.CONFIG, writeable=True)
    # unlock_setting (Normal=0, AutoUnlock=1, AlwaysLock=2)
    UST = ApiKey(key="ust", cat=CAT.CONFIG, writeable=True)
    # utc time
    UTC = ApiKey(key="utc", cat=CAT.STATUS, writeable=True)
    # variant: max Ampere value of unit (11: 11kW/16A, 22: 22kW/32A)
    VAR = ApiKey(key="var", cat=CAT.CONSTANT)
    # WiFi current mac address
    WCB = ApiKey(key="wcb", cat=CAT.STATUS)
    # WiFi failed mac addresses
    WFB = ApiKey(key="wfb", cat=CAT.STATUS)
    # energy in Wh since car connected
    WH = ApiKey(key="wh", cat=CAT.STATUS)
    # WiFi Konfiguration mit SSID und Passwort; Wenn man nur den zweiten Eintrag ändern möchte, einfach das erste Objekt leer lassen: [{}, {"ssid":"","key":""}]
    WIFIS = ApiKey(key="wifis", cat=CAT.CONFIG, writeable=True)
    # WiFi planned mac addresses
    WPB = ApiKey(key="wpb", cat=CAT.STATUS)
    # WiFi STA error count
    WSC = ApiKey(key="wsc", cat=CAT.STATUS)
    # WiFi STA error message
    WSM = ApiKey(key="wsm", cat=CAT.STATUS)
    # WiFi state machine state (None=0, Scanning=1, Connecting=2, Connected=3)
    WSMS = ApiKey(key="wsms", cat=CAT.STATUS)
    # WiFi STA status (IDLE_STATUS=0, NO_SSID_AVAIL=1, SCAN_COMPLETED=2, CONNECTED=3, CONNECT_FAILED=4, CONNECTION_LOST=5, DISCONNECTED=6, CONNECTING=8, DISCONNECTING=9, NO_SHIELD=10 (for compatibility with WiFi Shield library))
    WST = ApiKey(key="wst", cat=CAT.STATUS)
    # zeroFeedinOffset in W
    ZFO = ApiKey(key="zfo", cat=CAT.CONFIG, writeable=True)

    # undocumented PV-DATA-Write -> write a json object [{"pGrid": 1000., "pPv": 1000., "pAkku": 1000.}]
    # see also https://github.com/goecharger/go-eCharger-API-v2/discussions/110
    IDS = ApiKey(key="ids", cat=CAT.STATUS, writeable=True, writeonly=True)

    # none exsiting ApiKeys
    CAR_CONNECTED = ApiKey(key="car", cat=CAT.STATUS)
    INTERNAL_FORCE_CONFIG_READ = ApiKey(key="zfocore", cat=CAT.CONFIG)

    # NOT-DOCUMENTED
    # -> goe-Controller-Scan immer aktiviert
    CMSE = ApiKey(key="cmse", cat=CAT.CONFIG)
    # -> goe-Controller-Scan last scan time
    LCS = ApiKey(key="lcs", cat=CAT.CONFIG)

    # TODO: add #X keys...
    # rdbs | R/W | TYPE | Config | randomDelayStartScheduledCharging in seconds
    #"rdbs": 1, Random Start LoadTimer
    RDBS = ApiKey(key="rdbs", cat=CAT.CONFIG)
    # rdbse | R/W | TYPE | Config | randomDelayStartScheduledChargingEndsAt (set to null to abort current randomDelayStartScheduledCharging)
    #X RDBSE = ApiKey(key="rdbse", cat=CAT.CONFIG)

    # rdes | R/W | TYPE | Config | randomDelayStopScheduledCharging in seconds
    #"rdes": 2, Random End LoadTimer
    RDES = ApiKey(key="rdes", cat=CAT.CONFIG)
    # rdese | R/W | TYPE | Config | randomDelayStopScheduledChargingEndsAt (set to null to abort current randomDelayStopScheduledCharging)
    #X RDESE = ApiKey(key="rdese", cat=CAT.CONFIG)

    # rdbf | R/W | TYPE | Config | randomDelayStartFlexibleTariffCharging in seconds
    #"rdbf": 3, Flex Start
    RDBF = ApiKey(key="rdbf", cat=CAT.CONFIG)
    # rdbfe | R/W | TYPE | Config | randomDelayStartFlexibleTariffChargingEndsAt (set to null to abort current randomDelayStartFlexibleTariffCharging)
    #X RDBFE = ApiKey(key="rdbfe", cat=CAT.CONFIG)

    # rdef | R/W | TYPE | Config | randomDelayStopFlexibleTariffCharging in seconds
    #"rdef": 4, Flex End
    RDEF = ApiKey(key="rdef", cat=CAT.CONFIG)
    # rdefe | R/W | TYPE | Config | randomDelayStopFlexibleTariffChargingEndsAt (set to null to abort current randomDelayStopFlexibleTariffCharging)
    #X RDEFE = ApiKey(key="rdefe", cat=CAT.CONFIG)

    # rdre | R/W | TYPE | Config | randomDelayReconnection in seconds
    #"rdre": 5, after power off
    RDRE = ApiKey(key="rdre", cat=CAT.CONFIG)
    # rdree | R/W | TYPE | Config | randomDelayReconnectionEndsAt (set to null to abort current randomDelayReconnection)
    #X RDREE = ApiKey(key="rdree", cat=CAT.CONFIG)

    # rdpl | R/W | TYPE | Config | randomDelayWhenPluggingCar in seconds
    #"rdpl": 0, ????
    RDPL = ApiKey(key="rdpl", cat=CAT.CONFIG)
    # rdple | R/W | TYPE | Config | randomDelayWhenPluggingCarEndsAt (set to null to abort current randomDelayWhenPluggingCar)
    #X RDPLE = ApiKey(key="rdple", cat=CAT.CONFIG)


    #########################
    # NOT USED FROM HERE ON #
    #########################
    # color_charging, format: #RRGGBB
    CCH = ApiKey(key="cch", cat=CAT.CONFIG, writeable=True)
    # color_idle, format: #RRGGBB
    CID = ApiKey(key="cid", cat=CAT.CONFIG, writeable=True)
    # color_finished, format: #RRGGBB
    CFI = ApiKey(key="cfi", cat=CAT.CONFIG, writeable=True)
    # color_waitcar, format: #RRGGBB
    CWC = ApiKey(key="cwc", cat=CAT.CONFIG, writeable=True)
    # more Color keys added 2024/07/15
    #################################
    # ccd | R | TYPE | Status | Connected controller data cch | R/W | TYPE | Config | color_charging, format: #RRGGBB
    # t0h | R/W | TYPE | Config | led strip T0H
    # t0l | R/W | TYPE | Config | led strip T0L
    # t1h | R/W | TYPE | Config | led strip T1H
    # t1l | R/W | TYPE | Config | led strip T1L


    # OCPP connected and accepted
    OCPPA = ApiKey(key="ocppa", cat=CAT.STATUS)
    # OCPP connected and accepted (timestamp in milliseconds since reboot) Subtract from reboot time (rbt) to get number of milliseconds since connected
    OCPPAA = ApiKey(key="ocppaa", cat=CAT.STATUS)
    # OCPP connected
    OCPPC = ApiKey(key="ocppc", cat=CAT.STATUS)
    # OCPP connected (timestamp in milliseconds since reboot) Subtract from reboot time (rbt) to get number of milliseconds since connected
    OCPPCA = ApiKey(key="ocppca", cat=CAT.STATUS)
    # OCPP client cert
    OCPPCC = ApiKey(key="ocppcc", cat=CAT.CONFIG, writeable=True)
    # OCPP client key
    OCPPCK = ApiKey(key="ocppck", cat=CAT.CONFIG, writeable=True)
    # OCPP skipCertCommonNameCheck
    OCPPCN = ApiKey(key="ocppcn", cat=CAT.CONFIG, writeable=True)
    # OCPP dummy card id (used when no card has been used and charging is already allowed / starting)
    OCPPD = ApiKey(key="ocppd", cat=CAT.CONFIG, writeable=True)
    # OCPP enabled
    OCPPE = ApiKey(key="ocppe", cat=CAT.CONFIG, writeable=True)
    # OCPP use global CA Store
    OCPPG = ApiKey(key="ocppg", cat=CAT.CONFIG, writeable=True)
    # OCPP heartbeat interval (can also be read/written with GetConfiguration and ChangeConfiguration)
    OCPPH = ApiKey(key="ocpph", cat=CAT.CONFIG, writeable=True)
    # OCPP meter values sample interval (can also be read/written with GetConfiguration and ChangeConfiguration)
    OCPPI = ApiKey(key="ocppi", cat=CAT.CONFIG, writeable=True)
    # OCPP clock aligned data interval (can also be read/written with GetConfiguration and ChangeConfiguration)
    OCPPAI = ApiKey(key="ocppai", cat=CAT.CONFIG, writeable=True)
    # OCPP last error
    OCPPLE = ApiKey(key="ocpple", cat=CAT.STATUS)
    # OCPP last error (timestamp in milliseconds since reboot) Subtract from reboot time (rbt) to get number of milliseconds since connected
    OCPPLEA = ApiKey(key="ocpplea", cat=CAT.STATUS)
    # OCPP rotate phases on charger
    OCPPR = ApiKey(key="ocppr", cat=CAT.CONFIG, writeable=True)
    # OCPP remote logging (usually only enabled by go-e support to allow debugging)
    OCPPRL = ApiKey(key="ocpprl", cat=CAT.CONFIG, writeable=True)
    # OCPP started
    OCPPS = ApiKey(key="ocpps", cat=CAT.STATUS)
    # OCPP server cert
    OCPPSC = ApiKey(key="ocppsc", cat=CAT.CONFIG, writeable=True)
    # OCPP skipServerVerification
    OCPPSS = ApiKey(key="ocppss", cat=CAT.CONFIG, writeable=True)
    # OCPP server url
    OCPPU = ApiKey(key="ocppu", cat=CAT.CONFIG, writeable=True)

    # OCPP aktiviert
    #OCPPE = ApiKey(key="ocppe", cat=CAT.CONFIG, writeable=True)
    # OCPP server url
    #OCPPU = ApiKey(key="ocppu", cat=CAT.CONFIG, writeable=True)
    # OCPP use global CA Store
    #OCPPG = ApiKey(key="ocppg", cat=CAT.CONFIG, writeable=True)
    # OCPP skipCertCommonNameCheck
    #OCPPCN = ApiKey(key="ocppcn", cat=CAT.CONFIG, writeable=True)
    # OCPP skipServerVerification
    #OCPPSS = ApiKey(key="ocppss", cat=CAT.CONFIG, writeable=True)
    # OCPP gestartet
    #OCPPS = ApiKey(key="ocpps", cat=CAT.STATUS)
    # OCPP verbunden
    #OCPPC = ApiKey(key="ocppc", cat=CAT.STATUS)
    # OCPP verbunden (Zeitstempel in Millisekunden seit dem Hochfahren) Subtrahiere von der reboot-zeit (rbt) um die Dauer seit Verbunden zu erhalten
    #OCPPCA = ApiKey(key="ocppca", cat=CAT.STATUS)
    # OCPP verbunden und akzeptiert
    #OCPPA = ApiKey(key="ocppa", cat=CAT.STATUS)
    # OCPP verbunden und akzeptiert (Zeitstempel in Millisekunden seit dem Hochfahren) Subtrahiere von der reboot-zeit (rbt) um die Dauer seit Verbunden und akzeptiert zu erhalten
    #OCPPAA = ApiKey(key="ocppaa", cat=CAT.STATUS)
    # OCPP heartbeat interval (kann auch mit GetConfiguration und ChangeConfiguration gelesen/geschrieben werden)
    #OCPPH = ApiKey(key="ocpph", cat=CAT.CONFIG, writeable=True)
    # OCPP meter values sample interval (kann auch mit GetConfiguration und ChangeConfiguration gelesen/geschrieben werden)
    #OCPPI = ApiKey(key="ocppi", cat=CAT.CONFIG, writeable=True)
    # OCPP clock aligned data interval (kann auch mit GetConfiguration und ChangeConfiguration gelesen/geschrieben werden)
    #OCPPAI = ApiKey(key="ocppai", cat=CAT.CONFIG, writeable=True)
    # OCPP dummy card id (wird benutzt wenn keine Karte hingehalten wird und es schon erlaubt ist.
    #OCPPD = ApiKey(key="ocppd", cat=CAT.CONFIG, writeable=True)
    # OCPP rotate phases on charger
    #OCPPR = ApiKey(key="ocppr", cat=CAT.CONFIG, writeable=True)
    # OCPP letzter error
    #OCPPLE = ApiKey(key="ocpple", cat=CAT.STATUS)
    # OCPP letzter error (Zeitstempel in Millisekunden seit dem Hochfahren) Subtrahiere von der reboot-zeit (rbt) um die Dauer seit Error zu erhalten
    #OCPPLEA = ApiKey(key="ocpplea", cat=CAT.STATUS)
    # OCPP remote logging (usually only enabled by go-e support to allow debugging)
    #OCPPRL = ApiKey(key="ocpprl", cat=CAT.CONFIG, writeable=True)
    # OCPP client key
    #OCPPCK = ApiKey(key="ocppck", cat=CAT.CONFIG, writeable=True)
    # OCPP client cert
    #OCPPCC = ApiKey(key="ocppcc", cat=CAT.CONFIG, writeable=True)
    # OCPP server cert
    #OCPPSC = ApiKey(key="ocppsc", cat=CAT.CONFIG, writeable=True)

    # more OCPP keys added 2024/07/15
    #################################
    # ocppao | R/W | TYPE | Status | OCPP AllowOfflineTxForUnknownId
    # ocppcm | R/W | TYPE | Status | OCPP LocalAuthListEnabled
    # ocppcs | R | TYPE | Status | OCPP connector status (0=Available, 1=Preparing, 2=Charging, 3=SuspendedEVSE, 4=SuspendedEV, 5=Finishing, 6=Reserved, 7=Unavailable, 8=Faulted)
    # ocppf | R/W | TYPE | Config | OCPP fallback current
    # ocppla | R/W | TYPE | Status | OCPP LocalAuthListEnabled
    # ocpplo | R/W | TYPE | Status | OCPP LocalAuthorizeOffline
    # ocppti | R/W | TYPE | Status | OCPP transaction id


    # MQTT aktiviert
    MCE = ApiKey(key="mce", cat=CAT.CONFIG, writeable=True)
    # MQTT broker url
    MCU = ApiKey(key="mcu", cat=CAT.CONFIG, writeable=True)
    # MQTT readonly (erlaube kein Schreiben vom mqtt-broker aus)
    MCR = ApiKey(key="mcr", cat=CAT.CONFIG, writeable=True)
    # MQTT topic prefix (auf null setzen um auf Werkseinstellung zurückzusetzen)
    MTP = ApiKey(key="mtp", cat=CAT.CONFIG, writeable=True)
    # MQTT use global CA Store
    MQG = ApiKey(key="mqg", cat=CAT.CONFIG, writeable=True)
    # MQTT skipCertCommonNameCheck
    MQCN = ApiKey(key="mqcn", cat=CAT.CONFIG, writeable=True)
    # MQTT skipServerVerification
    MQSS = ApiKey(key="mqss", cat=CAT.CONFIG, writeable=True)
    # MQTT gestartet
    MCS = ApiKey(key="mcs", cat=CAT.STATUS)
    # MQTT verbunden
    MCC = ApiKey(key="mcc", cat=CAT.STATUS)
    # MQTT connected (Zeitstempel in Millisekunden seit dem Hochfahren) Subtrahiere von der reboot-zeit (rbt) um die Dauer seit Verbunden zu erhalten
    MCCA = ApiKey(key="mcca", cat=CAT.STATUS)
    # MQTT letzter error
    MLR = ApiKey(key="mlr", cat=CAT.STATUS)
    # MQTT last error (Zeitstempel in Millisekunden seit dem Hochfahren) Subtrahiere von der reboot-zeit (rbt) um die Dauer seit Error zu erhalten
    MLRA = ApiKey(key="mlra", cat=CAT.STATUS)
    # MQTT client key
    MCK = ApiKey(key="mck", cat=CAT.CONFIG, writeable=True)
    # MQTT client cert
    MQCC = ApiKey(key="mqcc", cat=CAT.CONFIG, writeable=True)
    # MQTT server cert
    MSC = ApiKey(key="msc", cat=CAT.CONFIG, writeable=True)

    # more MQTT keys added 2024/07/15
    #################################
    # mhe | R/W | TYPE | Config | MQTT enable homeassistant discovery
    # mht | R/W | TYPE | Config | MQTT homeassistant topic prefix (set to null to reset back to the default)


    # modbus slave aktiviert
    MEN = ApiKey(key="men", cat=CAT.CONFIG, writeable=True)
    # modbus slave port (erfordert Neustart)
    MSP = ApiKey(key="msp", cat=CAT.CONFIG, writeable=True)
    # modbus slave Bytes vertauschen
    MSB = ApiKey(key="msb", cat=CAT.CONFIG, writeable=True)
    # modbus slave Register vertauschen
    MSR = ApiKey(key="msr", cat=CAT.CONFIG, writeable=True)
    # modbus slave Lese-Operationen
    MRO = ApiKey(key="mro", cat=CAT.STATUS)
    # modbus slave Schreib-Operationen
    MWO = ApiKey(key="mwo", cat=CAT.STATUS)


    # NEW API keys 2024/07/15:
    #############################

    # avgfhz | R | TYPE | Status | Stromnetz average frequency (~50Hz)
    # awpl | W | TYPE | Status | awattar price list, timestamps are measured in unix-time, seconds since 1970
    # bar | R/W | TYPE | Config | Button Allow WiFi AP reset (0=AlwaysLock, 1=LockWhenCarIsConnected, 2=LockWhenCarIsCharging, 3=NeverLock)
    # cle | R | TYPE | Status | Cloud last error
    # clea | R | TYPE | Status | Cloud last error (age)


    # cmmr | R | TYPE | Config | controllerMdnsMaxResults
    # cmp | R | TYPE | Config | controllerMdnsProto
    # cms | R | TYPE | Config | controllerMdnsService
    # cmse | R | TYPE | Config | controllerMdnsScanEnabled, set to false to completely disable any MDNS searches (debugging)

    # csa | R | TYPE | Status | controller scan active
    # ct | R/W | TYPE | Config | car type, free text string (max. 64 characters)
    # ctrls | R | TYPE | Status | Controllers search result
    # data | R | TYPE | Status | grafana token from cloud for app
    # di1 | R/W | TYPE | Config | digital Input 1-phase
    # die | R/W | TYPE | Config | digital Input Enabled
    # dii | R/W | TYPE | Config | digital Input Inverted
    # dll | R | TYPE | Status | download link for app csv export
    # dsrc | R | TYPE | Status | inverter data source
    # gmtr | R/W | TYPE | Config | gridMonitoringTimeReconnection in seconds
    # gsa | R/W | TYPE | Status | gridMonitoring last failure
    # hai | R/W | TYPE | Config | httpApiEnabled (allows /api/status and /api/set requests)
    # hla | R/W | TYPE | Config | httpLegacyApiEnabled (allows /status and /mqtt requests)
    # la1 | R/W | TYPE | Config | limit adapter 1-phase (in A)
    # la3 | R/W | TYPE | Config | limit adapter 3-phase (in A)
    # lbl | R | TYPE | Config | lastButtonHoldLong
    # lcs | R | TYPE | Status | last controller scan timestamp in milliseconds since boot time
    # lopr | R/W | TYPE | Config | load balancing protected
    # lrc | R | TYPE | Status | last rfid card index
    # lri | R | TYPE | Status | last rfid id (only available when sendRfid)
    # lrr | R | TYPE | Status | last rfid read (milliseconds since boot)
    # lto | R | TYPE | Status | local time offset in milliseconds, tab + rbt + lto = local time
    # lwf | R | TYPE | Status | last wifi connect failed (milliseconds since boot)

    # pco | R | TYPE | Config | controllerCloudKey
    # pdi | R/W | TYPE | Config | protect Digital Input
    # pgr | R/W | TYPE | Config | protect Grid Requirements

    # rde | R/W | TYPE | Config | send rfid serial to cloud/api/mqtt (enable lri api key to show rfid numbers)

    # rmaf | R/W | TYPE | Config | reconnectionMaximumFrequency in Hz
    # rmav | R/W | TYPE | Config | reconnectionMaximumVoltage in Volt
    # rmif | R/W | TYPE | Config | reconnectionMinimumFrequency in Hz
    # rmiv | R/W | TYPE | Config | reconnectionMinimumVoltage in Volt

    # rsa | R/W | TYPE | Status | rampup started at
    # rsre | R/W | TYPE | Config | rampupAtStartAndReconnectionEnabled
    # rsrr | R/W | TYPE | Config | rampupAtStartAndReconnectionRate in %/s
    # smd | R | TYPE | Status | smart meter data
    # tab | R | TYPE | Status | time at boot in utc in milliseconds, add rbt to get to current utc time
    # tcl | R/W | TYPE | Config | temporary current limit (does not change the user current limit, will be reset after 10min if not updated regulary)
    # tsi | R | TYPE | Status | transaction start rfidid (only available when sendRfid)
    # tzt | R/W | TYPE | Config | timezone type, freetext string for app selection
    # ufa | R/W | TYPE | Config | Underfrequency Control activation threshold
    # ufe | R/W | TYPE | Config | Underfrequency Control enabled
    # ufm | R/W | TYPE | Config | Underfrequency Control mode (TypeNominal=0, TypeActual=1)
    # ufs | R/W | TYPE | Config | Underfrequency Control stop frequency
    # wbw | R | TYPE | Config | WiFi Bandwidth (for both AP and STA) WIFI_BW_HT20=1, WIFI_BW_HT40=2
    # wda | R/W | TYPE | Config | disable AccessPoint when cloud is connected
    # wsl | R | TYPE | Status | WiFi STA error messages log

    ###################################
    # CONTROLLER
    ###################################
    # https://github.com/goecharger/go-eController-API/blob/main/apikeys-en.md
    # rst | W | TYPE | Unknown | Reset the controller
    # RST = ApiKey(key="rst", cat=CAT.UNKNOWN, writeable=True)
    # -> exist
    # sse | R | TYPE | Constant | serial number
    # SSE = ApiKey(key="sse", cat=CAT.STATUS)
    # -> exist [no Sensor]
    # typ | R | TYPE | Constant | Devicetype
    # TYP = ApiKey(key="typ", cat=CAT.STATUS)
    # -> exist [no Sensor]
    # oem | R | TYPE | Constant | OEM manufacturer
    # OEM = ApiKey(key="oem", cat=CAT.STATUS)
    # -> exist [no Sensor]
    # fna | R/W | TYPE | Config | friendlyName
    # FNA = ApiKey(key="fna", cat=CAT.CONFIG, writeable=True)
    # -> exist [no Sensor]

    # hsa | W | TYPE | Config | httpStaAuthentication
    # HSA = ApiKey(key="hsa", cat=CAT.CONFIG, writeable=True)
    # oct | W | TYPE | Config | ota from cloud url trigger
    # OCT = ApiKey(key="oct", cat=CAT.CONFIG, writeable=True)
    # ccn | R/W | TYPE | Config | controller category names
    CCN = ApiKey(key="ccn", cat=CAT.CONFIG, writeable=True)
    # hai | R/W | TYPE | Config | httpApiEnabled (allows /api/status and /api/set requests)
    HAI = ApiKey(key="hai", cat=CAT.CONFIG, writeable=True)
    # wda | R/W | TYPE | Config | disable AccessPoint when cloud is connected
    WDA = ApiKey(key="wda", cat=CAT.CONFIG, writeable=True)
    # tse | R/W | TYPE | Config | time server enabled
    # TSE = ApiKey(key="tse", cat=CAT.CONFIG, writeable=True)
    # tof | R/W | TYPE | Config | timezone offset in minutes
    # TOF = ApiKey(key="tof", cat=CAT.CONFIG, writeable=True)
    # tds | R/W | TYPE | Config | timezone daylight saving mode, None=0, EuropeanSummerTime=1, UsDaylightTime=2
    # TDS = ApiKey(key="tds", cat=CAT.CONFIG, writeable=True)
    # awc | R/W | TYPE | Config | awattar country (Austria=0, Germany=1,...)
    # AWC = ApiKey(key="awc", cat=CAT.CONFIG, writeable=True)
    # awp | R/W | TYPE | Config | awattarMaxPrice in ct
    # AWP = ApiKey(key="awp", cat=CAT.CONFIG, writeable=True)
    # cwe | R/W | TYPE | Config | cloud websocket enabled
    # CWE = ApiKey(key="cwe", cat=CAT.CONFIG, writeable=True)
    # ocu | R | TYPE | Config | ota from cloud url, url to download new firmware code from
    # OCU = ApiKey(key="ocu", cat=CAT.CONFIG)
    # usn | R | TYPE | Config | voltage sensor names
    USN = ApiKey(key="usn", cat=CAT.CONFIG)
    # usv | R | TYPE | Status | voltage sensor values (use usn for sensor names)
    USV = ApiKey(key="usv", cat=CAT.STATUS)
    # isn | R | TYPE | Config | current sensor names
    ISN = ApiKey(key="isn", cat=CAT.CONFIG)
    # isv | R | TYPE | Config | current sensor values (use isn for sensors names)
    ISV = ApiKey(key="isv", cat=CAT.CONFIG)
    # ips | R/W | TYPE | Config | current phase selections (for every current sensor (api key isn) a phase selection, L1=0, L2=1, L3=2, N=3)
    IPS = ApiKey(key="ips", cat=CAT.CONFIG, writeable=True)
    # iim | R/W | TYPE | Config | invert current measurement (for every current sensor (api key isn) an invert flag)
    IIM = ApiKey(key="iim", cat=CAT.CONFIG, writeable=True)
    # mece | R/W | TYPE | Config | mecmeterEnabled
    MECE = ApiKey(key="mece", cat=CAT.CONFIG, writeable=True)
    # mecu | R/W | TYPE | Config | mecmeterUrl
    MECU = ApiKey(key="mecu", cat=CAT.CONFIG, writeable=True)
    # mme | R/W | TYPE | Config | modbus master enabled
    MME = ApiKey(key="mme", cat=CAT.CONFIG, writeable=True)
    # mmh | R/W | TYPE | Config | modbus master host
    MMH = ApiKey(key="mmh", cat=CAT.CONFIG, writeable=True)
    # mmp | R/W | TYPE | Config | modbus master port
    # MMP = ApiKey(key="mmp", cat=CAT.CONFIG, writeable=True)
    # men | R/W | TYPE | Config | modbus slave enabled
    # MEN = ApiKey(key="men", cat=CAT.CONFIG, writeable=True)
    # msp | R/W | TYPE | Config | modbus slave port (requires off/on toggle)
    # MSP = ApiKey(key="msp", cat=CAT.CONFIG, writeable=True)
    # msb | R/W | TYPE | Config | modbus slave swap bytes
    # MSB = ApiKey(key="msb", cat=CAT.CONFIG, writeable=True)
    # msr | R/W | TYPE | Config | modbus slave swap registers
    # MSR = ApiKey(key="msr", cat=CAT.CONFIG, writeable=True)
    # mce | R/W | TYPE | Config | MQTT enabled
    # MCE = ApiKey(key="mce", cat=CAT.CONFIG, writeable=True)
    # mcu | R/W | TYPE | Config | MQTT broker url
    # MCU = ApiKey(key="mcu", cat=CAT.CONFIG, writeable=True)
    # mcr | R/W | TYPE | Config | MQTT readonly (don't allow api writes from mqtt broker)
    # MCR = ApiKey(key="mcr", cat=CAT.CONFIG, writeable=True)
    # mtp | R/W | TYPE | Config | MQTT topic prefix (set to null to reset back to the default)
    # MTP = ApiKey(key="mtp", cat=CAT.CONFIG, writeable=True)
    # mqg | R/W | TYPE | Config | MQTT useGlobalCaStore
    # MQG = ApiKey(key="mqg", cat=CAT.CONFIG, writeable=True)
    # mqcn | R/W | TYPE | Config | MQTT skipCertCommonNameCheck
    # MQCN = ApiKey(key="mqcn", cat=CAT.CONFIG, writeable=True)
    # mqss | R/W | TYPE | Config | MQTT skipServerVerification
    # MQSS = ApiKey(key="mqss", cat=CAT.CONFIG, writeable=True)
    # wifis | R/W | TYPE | Config | wifi configurations with ssids and keys, if you only want to change the second entry, send an array with 1 empty and 1 filled wifi config object: [{}, {"ssid":"","key":""}]
    # WIFIS = ApiKey(key="wifis", cat=CAT.CONFIG, writeable=True)
    # utc | R/W | TYPE | Status | utc time
    # UTC = ApiKey(key="utc", cat=CAT.STATUS, writeable=True)
    # ccf | R/W | TYPE | Status | Controller category factors (outer array defines the current sensors, use isn for for current sensor names, the inner arrays are for each category, use ccn for the category names)
    CCF = ApiKey(key="ccf", cat=CAT.STATUS, writeable=True)
    # mecf | R/W | TYPE | Status | Mecmeter category factors (outer array defines the 3 mecmeter loads, the inner arrays are for each category, use ccn for the category names)
    MECF = ApiKey(key="mecf", cat=CAT.STATUS, writeable=True)
    # scan | R | TYPE | Status | wifi scan result (encryptionType: OPEN=0, WEP=1, WPA_PSK=2, WPA2_PSK=3, WPA_WPA2_PSK=4, WPA2_ENTERPRISE=5, WPA3_PSK=6, WPA2_WPA3_PSK=7)
    # SCAN = ApiKey(key="scan", cat=CAT.STATUS)
    # lwf | R | TYPE | Status | last wifi connect failed (milliseconds since boot)
    LWF = ApiKey(key="lwf", cat=CAT.STATUS)
    # scaa | R | TYPE | Status | wifi scan age
    # SCAA = ApiKey(key="scaa", cat=CAT.STATUS)
    # wst | R | TYPE | Status | WiFi STA status (IDLE_STATUS=0, NO_SSID_AVAIL=1, SCAN_COMPLETED=2, CONNECTED=3, CONNECT_FAILED=4, CONNECTION_LOST=5, DISCONNECTED=6, CONNECTING=7, DISCONNECTING=8, NO_SHIELD=9, WAITING_FOR_IP=10)
    # WST = ApiKey(key="wst", cat=CAT.STATUS)
    # wsc | R | TYPE | Status | WiFi STA error count
    # WSC = ApiKey(key="wsc", cat=CAT.STATUS)
    # wsm | R | TYPE | Status | WiFi STA error message
    # WSM = ApiKey(key="wsm", cat=CAT.STATUS)
    # wsl | R | TYPE | Status | WiFi STA error messages log
    WSL = ApiKey(key="wsl", cat=CAT.STATUS)
    # wsms | R | TYPE | Status | WiFi state machine state (None=0, Scanning=1, Connecting=2, Connected=3)
    # WSMS = ApiKey(key="wsms", cat=CAT.STATUS)
    # ccw | R | TYPE | Status | Currently connected WiFi
    # CCW = ApiKey(key="ccw", cat=CAT.STATUS)
    # wfb | R | TYPE | Status | WiFi failed mac addresses (bssids)
    # WFB = ApiKey(key="wfb", cat=CAT.STATUS)
    # wcb | R | TYPE | Status | WiFi current mac address (bssid connecting to)
    # WCB = ApiKey(key="wcb", cat=CAT.STATUS)
    # wpb | R | TYPE | Status | WiFi planned mac addresses (future bssids)
    # WPB = ApiKey(key="wpb", cat=CAT.STATUS)
    # nif | R | TYPE | Status | Default route
    # NIF = ApiKey(key="nif", cat=CAT.STATUS)
    # cce | R | TYPE | Status | Currently connected Ethernet
    CCE = ApiKey(key="cce", cat=CAT.STATUS)
    # dns | R | TYPE | Status | dns servers
    # DNS = ApiKey(key="dns", cat=CAT.STATUS)
    # rssi | R | TYPE | Status | RSSI signal strength
    # RSSI = ApiKey(key="rssi", cat=CAT.STATUS)
    # tsss | R | TYPE | Status | time server sync status (RESET=0, COMPLETED=1, IN_PROGRESS=2)
    # TSSS = ApiKey(key="tsss", cat=CAT.STATUS)
    # loc | R | TYPE | Status | local time
    # LOC = ApiKey(key="loc", cat=CAT.STATUS)
    # rbc | R | TYPE | Status | reboot_counter
    # RBC = ApiKey(key="rbc", cat=CAT.STATUS)
    # rbt | R | TYPE | Status | time since boot in milliseconds
    # RBT = ApiKey(key="rbt", cat=CAT.STATUS)
    # fwv | R | TYPE | Status | FW_VERSION
    # FWV = ApiKey(key="fwv", cat=CAT.STATUS)
    # awcp | R | TYPE | Status | awattar current price
    # AWCP = ApiKey(key="awcp", cat=CAT.STATUS)
    # awpl | W | TYPE | Status | awattar price list, timestamps are measured in unix-time, seconds since 1970
    AWPL = ApiKey(key="awpl", cat=CAT.STATUS, writeable=True)
    # clea | R | TYPE | Status | Cloud last error (age)
    CLEA = ApiKey(key="clea", cat=CAT.STATUS)
    # cle | R | TYPE | Status | Cloud last error
    CLE = ApiKey(key="cle", cat=CAT.STATUS)
    # data | R | TYPE | Status | grafana token from cloud for app
    DATA = ApiKey(key="data", cat=CAT.STATUS)
    # dll | R | TYPE | Status | download link for app csv export
    DLL = ApiKey(key="dll", cat=CAT.STATUS)
    # mcs | R | TYPE | Status | MQTT started
    # MCS = ApiKey(key="mcs", cat=CAT.STATUS)
    # mcc | R | TYPE | Status | MQTT connected
    # MCC = ApiKey(key="mcc", cat=CAT.STATUS)
    # mcca | R | TYPE | Status | MQTT connected (age)
    # MCCA = ApiKey(key="mcca", cat=CAT.STATUS)
    # mlr | R | TYPE | Status | MQTT last error
    # MLR = ApiKey(key="mlr", cat=CAT.STATUS)
    # mlra | R | TYPE | Status | MQTT last error (age)
    # MLRA = ApiKey(key="mlra", cat=CAT.STATUS)
    # ccp | R | TYPE | Status | controller category powers
    CCP = ApiKey(key="ccp", cat=CAT.STATUS)
    # cec | R | TYPE | Status | controller energy counters
    CEC = ApiKey(key="cec", cat=CAT.STATUS)
    # cpc | R | TYPE | Status | controller category phase currents
    CPC = ApiKey(key="cpc", cat=CAT.STATUS)
    # bri | R | TYPE | Status | brightness sensor
    BRI = ApiKey(key="bri", cat=CAT.STATUS)
    # mecd | R | TYPE | Status | Mecmeter current data
    MECD = ApiKey(key="mecd", cat=CAT.STATUS)

    # delw | W | TYPE | Unknown | set this to 0-9 to delete sta config (erases ssid, key, ...)
    # DELW = ApiKey(key="delw", cat=CAT.UNKNOWN, writeable=True)

    # host | R | TYPE | Status | configured hostname
    # HOST = ApiKey(key="host", cat=CAT.STATUS)
    # -> exist as KEY but does not EXIST in GOe API responses :-/



    # hsa | W | TYPE | Config | httpStaAuthentication
    # oct | W | TYPE | Config | ota from cloud url trigger
    # ccn | R/W | TYPE | Config | controller category names
    # hai | R/W | TYPE | Config | httpApiEnabled (allows /api/status and /api/set requests)
    # wda | R/W | TYPE | Config | disable AccessPoint when cloud is connected
    # tse | R/W | TYPE | Config | time server enabled
    # tof | R/W | TYPE | Config | timezone offset in minutes
    # tds | R/W | TYPE | Config | timezone daylight saving mode, None=0, EuropeanSummerTime=1, UsDaylightTime=2
    # awc | R/W | TYPE | Config | awattar country (Austria=0, Germany=1,...)
    # awp | R/W | TYPE | Config | awattarMaxPrice in ct
    # cwe | R/W | TYPE | Config | cloud websocket enabled
    # ocu | R | TYPE | Config | ota from cloud url, url to download new firmware code from
    # usn | R | TYPE | Config | voltage sensor names
    # usv | R | TYPE | Status | voltage sensor values (use usn for sensor names)
    # isn | R | TYPE | Config | current sensor names
    # isv | R | TYPE | Config | current sensor values (use isn for sensors names)
    # ips | R/W | TYPE | Config | current phase selections (for every current sensor (api key isn) a phase selection, L1=0, L2=1, L3=2, N=3)
    # iim | R/W | TYPE | Config | invert current measurement (for every current sensor (api key isn) an invert flag)
    # mece | R/W | TYPE | Config | mecmeterEnabled
    # mecu | R/W | TYPE | Config | mecmeterUrl

    # mme | R/W | TYPE | Config | modbus master enabled
    # mmh | R/W | TYPE | Config | modbus master host
    # mmp | R/W | TYPE | Config | modbus master port
    # men | R/W | TYPE | Config | modbus slave enabled
    # msp | R/W | TYPE | Config | modbus slave port (requires off/on toggle)
    # msb | R/W | TYPE | Config | modbus slave swap bytes
    # msr | R/W | TYPE | Config | modbus slave swap registers

    # mce | R/W | TYPE | Config | MQTT enabled
    # mcu | R/W | TYPE | Config | MQTT broker url
    # mcr | R/W | TYPE | Config | MQTT readonly (don't allow api writes from mqtt broker)
    # mtp | R/W | TYPE | Config | MQTT topic prefix (set to null to reset back to the default)
    # mqg | R/W | TYPE | Config | MQTT useGlobalCaStore
    # mqcn | R/W | TYPE | Config | MQTT skipCertCommonNameCheck
    # mqss | R/W | TYPE | Config | MQTT skipServerVerification

    # wifis | R/W | TYPE | Config | wifi configurations with ssids and keys, if you only want to change the second entry, send an array with 1 empty and 1 filled wifi config object: [{}, {"ssid":"","key":""}]

    # utc | R/W | TYPE | Status | utc time
    # ccf | R/W | TYPE | Status | Controller category factors (outer array defines the current sensors, use isn for for current sensor names, the inner arrays are for each category, use ccn for the category names)
    # mecf | R/W | TYPE | Status | Mecmeter category factors (outer array defines the 3 mecmeter loads, the inner arrays are for each category, use ccn for the category names)

    # scan | R | TYPE | Status | wifi scan result (encryptionType: OPEN=0, WEP=1, WPA_PSK=2, WPA2_PSK=3, WPA_WPA2_PSK=4, WPA2_ENTERPRISE=5, WPA3_PSK=6, WPA2_WPA3_PSK=7)
    # lwf | R | TYPE | Status | last wifi connect failed (milliseconds since boot)
    # scaa | R | TYPE | Status | wifi scan age
    # wst | R | TYPE | Status | WiFi STA status (IDLE_STATUS=0, NO_SSID_AVAIL=1, SCAN_COMPLETED=2, CONNECTED=3, CONNECT_FAILED=4, CONNECTION_LOST=5, DISCONNECTED=6, CONNECTING=7, DISCONNECTING=8, NO_SHIELD=9, WAITING_FOR_IP=10)
    # wsc | R | TYPE | Status | WiFi STA error count
    # wsm | R | TYPE | Status | WiFi STA error message
    # wsl | R | TYPE | Status | WiFi STA error messages log
    # wsms | R | TYPE | Status | WiFi state machine state (None=0, Scanning=1, Connecting=2, Connected=3)
    # ccw | R | TYPE | Status | Currently connected WiFi
    # wfb | R | TYPE | Status | WiFi failed mac addresses (bssids)
    # wcb | R | TYPE | Status | WiFi current mac address (bssid connecting to)
    # wpb | R | TYPE | Status | WiFi planned mac addresses (future bssids)
    # nif | R | TYPE | Status | Default route
    # cce | R | TYPE | Status | Currently connected Ethernet
    # dns | R | TYPE | Status | dns servers
    # rssi | R | TYPE | Status | RSSI signal strength
    # tsss | R | TYPE | Status | time server sync status (RESET=0, COMPLETED=1, IN_PROGRESS=2)
    # loc | R | TYPE | Status | local time
    # rbc | R | TYPE | Status | reboot_counter
    # rbt | R | TYPE | Status | time since boot in milliseconds
    # fwv | R | TYPE | Status | FW_VERSION
    # awcp | R | TYPE | Status | awattar current price
    # awpl | W | TYPE | Status | awattar price list, timestamps are measured in unix-time, seconds since 1970
    # clea | R | TYPE | Status | Cloud last error (age)
    # cle | R | TYPE | Status | Cloud last error
    # data | R | TYPE | Status | grafana token from cloud for app
    # dll | R | TYPE | Status | download link for app csv export
    # mcs | R | TYPE | Status | MQTT started
    # mcc | R | TYPE | Status | MQTT connected
    # mcca | R | TYPE | Status | MQTT connected (age)
    # mlr | R | TYPE | Status | MQTT last error
    # mlra | R | TYPE | Status | MQTT last error (age)
    # ccp | R | TYPE | Status | controller category powers
    # cec | R | TYPE | Status | controller energy counters
    # cpc | R | TYPE | Status | controller category phase currents
    # bri | R | TYPE | Status | brightness sensor
    # mecd | R | TYPE | Status | Mecmeter current data

    # delw | W | TYPE | Unknown | set this to 0-9 to delete sta config (erases ssid, key, ...)

    # host | R | TYPE | Status | configured hostname
    # -> exist as KEY but does not EXIST in GOe API responses :-/
