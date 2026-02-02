from enum import Enum
from typing import Final

##############
#   CHARGER  #
##############
FILTER_CARDS_ID_CLASSIC: Final  = "cards"
FILTER_CARDS_NAME_CLASSIC: Final = FILTER_CARDS_ID_CLASSIC
FILTER_CARDS_ENGY_CLASSIC: Final = FILTER_CARDS_ID_CLASSIC
FILTER_CARDS_ALL_CLASSIC: Final = FILTER_CARDS_ID_CLASSIC

FILTER_CARDS_ID_FWV60: Final  = "c0i,c1i,c2i,c3i,c4i,c5i,c6i,c7i,c8i,c9i"
FILTER_CARDS_NAME_FWV60: Final= "c0n,c1n,c2n,c3n,c4n,c5n,c6n,c7n,c8n,c9n"
FILTER_CARDS_ENGY_FWV60: Final= "c0e,c1e,c2e,c3e,c4e,c5e,c6e,c7e,c8e,c9e"
FILTER_CARDS_ALL_FWV60: Final = f"{FILTER_CARDS_ID_FWV60},{FILTER_CARDS_NAME_FWV60},{FILTER_CARDS_ENGY_FWV60}"

FILTER_SYSTEMS: Final = "oem,sse,typ,var"
FILTER_VERSIONS: Final = f"ccrv,fwc,fwv,var,{FILTER_CARDS_ID_CLASSIC},{FILTER_CARDS_ID_FWV60}"
FILTER_MIN_STATES: Final = "car,modelStatus,err,nrg,tma,trx"
FILTER_IDS_ADDON: Final = ",pakku,ppv,pgrid"

# rbt: is the reboot time - and "looks like", that all other timestamps use the rbt "as" start point
FILTER_TIMES_ADDON: Final = ",rbt,fsptws,inva,lbp,lccfc,lccfi,lcctc,lfspt,lmsc,lpsc,lcs"

FILTER_ALL_STATES_1: Final = "alw,acu,adi,amt,atp,awcp,car,{CARDS_ENERGY_FILTER},cbl,ccu,ccw,cdi,cll,cus,ctrls,deltaa,deltap,di1,err,eto,ffb,fhz,fsp,fsptws,inva,lbp,lccfc"
FILTER_ALL_STATES_2: Final = "lccfi,lcctc,lck,lfspt,lmsc,loa,lpsc,mcpea,mmp,modelStatus,nif,nrg,pakku,pgrid,pha,pnp,ppv,pvopt_averagePAkku,pvopt_averagePGrid,pvopt_averagePPv,pwm,rbc,rbt,rfb,rssi,rst,tlf,tls,tma,tpa,trx,wh,wsms,wst"
FILTER_ALL_STATES: Final = [FILTER_ALL_STATES_1, FILTER_ALL_STATES_2]
FILTER_ALL_CONFIG_1: Final = "acp,acs,ama,amp,ara,ate,att,awc,awe,awp,bac,{CARDS_ID_FILTER},cch,cco,cfi,cid,clp,cmse,ct,cwc,cwe,dwo,esk"
FILTER_ALL_CONFIG_2: Final = "fmt,fna,frc,frm,fst,fup,fzf,hsa,lbr,lmo,loe,lof,log,lop,lot,loty,lse,map,mca,mci,mcpd,mptwt,mpwst,nmo,pgt,po,psh,psm,psmd,rdbf,rdbs,rdef,rdes,rdre,rdpl,sch_satur,sch_sund,sch_week,sdp,sh,spl3,su,sua,sumd,tds,tof,upo,ust,zfo"
FILTER_ALL_CONFIG: Final = [FILTER_ALL_CONFIG_1, FILTER_ALL_CONFIG_2]

FILTER_NOT_USED: Final = "mcc,mcca,mce,mcr,mcs,mcu,men,mlr,mlra,mqcn,mqg,mqss,msb,msp,msr,mtp,ocppai,ocppi,rdbfe,rdbse,rdefe,rdese,rdree,rdple"

# found api-keys that are not documented (yet) ?!
FILTER_UNKNOWN_COMON: Final = "aus,ccd,cle,clea,cmmr,cmp,cms,csa,data,die,dii,dll,hai,hla,isgo,la1,la3,lbl,lopr,lrc,lri,lrr,lwf,ocppao,ocppcm,ocppcs,ocppf,ocppla,ocpplo,ocppti,pdi,pgr,rde,smd,tcl,tsi,tzt,ufa,ufe,ufm,ufs,wbw,wda,wsl"

FILTER_UNKNOWN_FW59_X_BETA: Final = "bar,dsrc,evt,gmtr,gsa,lto,mhe,mht,ocppdp,ocppmp,ocpptp,orsch,pco,rdbfe,rdbse,rdefe,rdese,rdple,rdree,rmaf,rmav,rmif,rmiv,rsa,rsre,rsrr,tab"
FILTER_UNKNOWN_FW56_2_BETA: Final = "bar,gmtr,gsa,mhe,mht,pco,rmaf,rmav,rmif,rmiv,rsa,rsre,rsrr"
FILTER_UNKNOWN_FW56_1: Final = "avgfhz,simo"

##############
# CONTROLLER #
##############
FILTER_CONTROLER_SYSTEMS: Final = "oem,sse,typ,fna"
FILTER_CONTROLER_VERSIONS: Final = "fwv"
FILTER_CONTROLER_MIN_STATES: Final = "usv,isv,cec,ccp"

# rbt: is the reboot time - and "looks like", that all other timestamps use the rbt "as" start point
FILTER_CONTROLER_TIMES_ADDON: Final = ",rbt,lcs,clea"
FILTER_CONTROLER_ALL_STATES: Final = "usv,isv,ccp,ecp,cec,cpc,ccf,ccw,wst"
FILTER_CONTROLER_ALL_CONFIG: Final = "mece,mecu,hai,wda,mme,mmh,iim,ips"


class INTG_TYPE(Enum):
    CHARGER = "charger"
    CONTROLLER = "controller"

class CAR_VALUES(Enum):
    UNKNOWN = 0
    IDLE = 1
    CHARGING = 2
    WAIT_FOR_CAR = 3
    COMPLETE = 4
    ERROR = 5

# compatibility car list... will set 'ct' value and 'su' true/false (true when ct != default)

class CT_VALUES(Enum):
    DEFAULT         = "default"
    KIASOUL         = "kiasoul"
    RENAULTZOE      = "renaultzoe"
    MITSUBISHIIMIEV = "mitsubishiimiev"
    CITROENCZERO    = "citroenczero"
    PEUGEOTION      = "peugeotion"

CT_VALUES_MAP: Final = {
    CT_VALUES.DEFAULT.value:          "default",
    CT_VALUES.KIASOUL.value:          "kiaSoul",
    CT_VALUES.RENAULTZOE.value:       "renaultZoe",
    CT_VALUES.MITSUBISHIIMIEV.value:  "MitsubishiImiev",
    CT_VALUES.CITROENCZERO.value:     "citroenCZero",
    CT_VALUES.PEUGEOTION.value:       "peugeotIon",
}

TRANSLATIONS: Final = {
    "de": {
        "car": {
            0: "Unbekannt/Fehler",
            1: "Inaktiv/Frei",
            2: "Laden",
            3: "Warte auf Fahrzeug",
            4: "Abgeschlossen",
            5: "Fehler",
        },
        "cus": {
            0: "Unbekannt",
            1: "Entriegelt",
            2: "Entriegelung fehlgeschlagen",
            3: "Verriegelt",
            4: "Verriegelung fehlgeschlagen",
            5: "Ver/Entriegelung Stromausfall",
        },
        "err": {
            0: "-keiner-",
            1: "Fi-AC Fehler",
            2: "Fi-DC Fehler",
            3: "Phasen Fehler",
            4: "Überspannung",
            5: "Überstrom",
            6: "Diode",
            7: "Pp ungültig",
            8: "Keine Masse",
            9: "Schutz klemmt",
            10: "Schutz fehlt",
            11: "Fi unbekannt",
            12: "Unbekannt",
            13: "Überhitzt",
            14: "Keine Kommunikation",
            15: "Verriegelung klemmt (offen)",
            16: "Entriegelung klemmt (gesperrt)",
            17: "?unbekannt?",
            18: "?unbekannt?",
            19: "?unbekannt?",
            20: "Reserviert20",
            21: "Reserviert21",
            22: "Reserviert22",
            23: "Reserviert23",
            24: "Reserviert24",
        },

        # LOADING-Strings...
        # Laden mit internen Fehler

        # NOT-LOADING-Strings
        # Nicht laden im aWATTar Modus
        # Nicht laden im geplanter Ladevorgang Modus
        # Nicht laden, Ladevorgang auf später verschoben
        # Laden gestoppt durch OCPP Backend
        # Laden gestoppt durch zufällige Verzögerung

        # USED/Mapes--Strings:
        # Laden im Ladetimer Modus
        # Laden im Standard Modus
        # Laden mit günstigen aWATTar Preis
        # Laden mit geplanten Ladevorgang, nicht mehr ausreichend Zeit
        # Laden mit geplanten Ladevorgang, keine Uhrzeit
        # Laden mit geplanten Ladevorgang, Testladung
        # Laden mit geplanten Ladevorgang
        # Laden um das Auto wach zu halten
        # Laden weil Ladepause nicht erlaubt
        # Laden mit PV Überschuss
        # Laden manuell freigegeben
        # Nicht laden, durch Ladetimer gestoppt
        # Nicht laden weil kWh Limit erreicht
        # Nicht laden, manuell gestoppt
        # Nicht laden, warte auf Zugangskontrolle
        # Nicht laden weil Übertemperatur
        # Nicht laden, ausstecken simulieren
        # Nicht laden während der Phasenumschaltung
        # Nicht laden, warte minimale Ladepause ab

        # 'geplanten Ladevorgang' -> Next-Trip Modus
        "modelstatus": {
            0: "Nicht laden, weil 'no charge control data'",
            1: "Nicht laden wegen Überhitzung",
            2: "Nicht laden, warte auf Zugangskontrolle",
            3: "Laden manuell freigegeben",
            4: "Nicht laden, da manuell gestoppt",
            5: "Nicht laden, durch Ladetimer gestoppt",
            6: "Nicht laden weil kWh Limit erreicht",
            7: "Laden mit günstigem Strompreis",
            8: "Laden im Next-Trip Modus, Testladung",
            9: "Laden im Next-Trip Modus, keine Uhrzeit",
            10: "Laden im Next-Trip Modus",
            11: "Laden im Next-Trip Modus, nicht mehr ausreichend Zeit",
            12: "Laden mit PV Überschuss",
            13: "Laden im Standard Modus (go-e Default)",
            14: "Laden im Ladetimer Modus (go-e Scheduler)",
            15: "Laden weil 'fallback (Default)'",
            16: "Nicht laden, weil 'Fallback (go-e günstiger Strompreis)'",
            17: "Nicht laden, weil 'Fallback (günstiger Strompreis)'",
            18: "Nicht laden, weil 'Fallback (Automatic Stop)'",
            19: "Laden um das Auto wach zu halten",
            20: "Laden weil Ladepause nicht erlaubt",
            21: "?unbekannt?",
            22: "Nicht laden, ausstecken simulieren",
            23: "Nicht laden während der Phasenumschaltung",
            24: "Nicht laden, warte minimale Ladepause ab",
            25: "?unbekannt?",
            26: "Nicht laden, wegen Fehler",
            27: "Nicht laden, weil vom Lastmanagement abgelehnt",
            28: "Nicht laden, weil vom OCPP abgelehnt",
            29: "Nicht laden, wegen Reconnect Verzögerung",
            30: "Nicht laden, weil der Adapter es blokiert",
            31: "Nicht laden, wegen der 'Under frequency Control'",
            32: "Nicht laden, wegen 'Unbalanced Load'",
            33: "Nicht laden, wegen Entladung der PV Batterie",
            34: "Nicht laden, wegen 'Grid Monitoring'",
            35: "Nicht laden, wegen 'OCPP Fallback'",
            36: "?unbekannt?",
            37: "?unbekannt?",
            38: "?unbekannt?",
            39: "?unbekannt?",
            40: "?unbekannt?"
        },
        "ffb": {
            0: "Kein Problem",
            1: "Problem beim Verriegeln",
            2: "Problem beim Entriegeln"
        },
        "frm": {
            0: "Netzbezug bevorzugen",
            1: "Default",
            2: "Netzeinspeisung bevorzugen"
        },
        "lck": {
            0: "Normal",
            1: "Auto entriegeln",
            2: "Immer verriegeln",
            3: "Entriegeln erzwingen"
        },
        "pwm": {
            0: "3-Phasen erzwingen",
            1: "Wenn möglich 1-Phase",
            2: "Wenn möglich 3-Phasen"
        },
        "wsms": {
            0: "keiner",
            1: "scann",
            2: "verbinde",
            3: "verbunden"
        },
        "wst": {
            0: "inaktiv/idle",
            1: "Keine SSID verfügbar",
            2: "Scan abgeschlossen",
            3: "verbunden",
            4: "Verbindung fehlgeschlagen",
            5: "Verbindung verloren",
            6: "getrennt",
            7: "?unbekannt?",
            8: "verbinde",
            9: "trenne",
            10: "Kein Schild/No shield"
        },

        "cll_accesscontrol": "Autorisierung",
        "cll_cablecurrentlimit": "Stromlimit Kabel",
        "cll_currentlimitmax": "Max. Ladestrom",
        "cll_minchargingcurrent": "Min. Ladestrom",
        "cll_requestedcurrent": "Angeforderter Ladestrom",
        "cll_temperaturecurrentlimit": "Stromlimit Temperatur",
        "cll_unsymetrycurrentlimit": "Stromlimit Asymmetrie"
    },
    "en": {
        "car": {
            0: "Unknown/Error",
            1: "Idle",
            2: "Charging",
            3: "Wait for car",
            4: "Complete",
            5: "Error",
        },
        "cus": {
            0: "Unknown",
            1: "Unlocked",
            2: "Unlock failed",
            3: "Locked",
            4: "Lock failed",
            5: "Lock/Unlock power outage",
        },
        "err": {
            0: "-none-",
            1: "FI AC fault",
            2: "FI DC fault",
            3: "Phase fault",
            4: "Over voltage",
            5: "Over current",
            6: "Diode",
            7: "PP invalid",
            8: "Ground invalid",
            9: "Contactor stuck",
            10: "Contactor missing",
            11: "FI unknown",
            12: "Unknown",
            13: "Over temperature",
            14: "No communication",
            15: "Lock stuck open",
            16: "Lock stuck locked",
            17: "?unknown?",
            18: "?unknown?",
            19: "?unknown?",
            20: "Reserved20",
            21: "Reserved21",
            22: "Reserved22",
            23: "Reserved23",
            24: "Reserved24"
        },
        # 'automatic stop' -> 'Next-Trip Mode'
        "modelstatus": {
            0: "Not charging because no charge control data",
            1: "Not charging because of over temperature",
            2: "Not charging because access control wait",
            3: "Charging because of forced state 'on'",
            4: "Not charging because of forced state 'off'",
            5: "Not charging because of scheduler",
            6: "Not charging because of energy limit",
            7: "Charging because Awattar price below threshold",
            8: "Charging because of automatic stop, test charging",
            9: "Charging because of automatic stop, not enough time",
            10: "Charging because of automatic stop",
            11: "Charging because of automatic stop, no clock",
            12: "Charging because of PV surplus",
            13: "Charging because of fallback (go-e default)",
            14: "Charging because of fallback (go-e scheduler)",
            15: "Charging because of fallback (default)",
            16: "Not charging because of fallback (go-e Awattar)",
            17: "Not charging because of fallback (Awattar)",
            18: "Not charging because of fallback (automatic stop)",
            19: "Charging because of car compatibility (keep alive)",
            20: "Charging because charge pause not allowed",
            21: "?unknown?",
            22: "Not charging because of simulate unplugging",
            23: "Not charging because of phase switch",
            24: "Not charging because of minimum pause duration",
            25: "?unknown?",
            26: "Not charging because of error",
            27: "Not charging because of load management doesn't want",
            28: "Not charging because of OCPP doesn't want",
            29: "Not charging because of reconnect delay",
            30: "Not charging because of adapter blocking",
            31: "Not charging because of under frequency control",
            32: "Not charging because of unbalanced load",
            33: "Not charging because of discharging PV battery",
            34: "Not charging because of grid monitoring",
            35: "Not charging because of OCPP fallback",
            36: "?unknown?",
            37: "?unknown?",
            38: "?unknown?",
            39: "?unknown?",
            40: "?unknown?"
        },
        "ffb": {
            0: "No problem",
            1: "Problem with lock",
            2: "Problem with unlock"
        },
        "frm": {
            0: "Prefer power import from grid",
            1: "Default",
            2: "Prefer power export to grid"
        },
        "lck": {
            0: "Normal",
            1: "Auto unlock",
            2: "Always lock",
            3: "Force unlock"
        },
        "pwm": {
            0: "Force 3-Phases",
            1: "Wish 1-Phase",
            2: "Wish 3-Phases"
        },
        "wsms": {
            0: "None",
            1: "Scanning",
            2: "Connecting",
            3: "Connected"
        },
        "wst": {
            0: "Idle status",
            1: "No SSID available",
            2: "Scan completed",
            3: "Connected",
            4: "Connect failed",
            5: "Connection lost",
            6: "Disconnected",
            7: "?unknown?",
            8: "Connecting",
            9: "Disconnecting",
            10: "No shield"
        },

        "cll_accesscontrol": "Access Control",
        "cll_cablecurrentlimit": "Current-limit Cable",
        "cll_currentlimitmax": "Max charging Current",
        "cll_minchargingcurrent": "Min. charging Current",
        "cll_requestedcurrent": "Requested Current",
        "cll_temperaturecurrentlimit": "Current-limit Temperature",
        "cll_unsymetrycurrentlimit": "Current-limit Unsymetry"
    }
}