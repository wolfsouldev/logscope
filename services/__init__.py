# services/__init__.py
from services.squid import SquidAnalyzer
from services.nginx import NginxAnalyzer
from services.pihole import PiholeAnalyzer
from services.adguard import AdGuardAnalyzer
from services.custom import CustomAnalyzer

SERVICE_MAP = {
    "squid":   SquidAnalyzer,
    "nginx":   NginxAnalyzer,
    "pihole":  PiholeAnalyzer,
    "adguard": AdGuardAnalyzer,
    "custom":  CustomAnalyzer,
}
