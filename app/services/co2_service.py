"""주행거리 기반 CO2 절감량 계산 (백엔드 결정적 계산).

수소 전기차 주행은 내연기관 대비 주행 중 CO2 배출이 없으므로, 동일 거리를
내연기관으로 주행했을 때의 배출량을 "절감량"으로 환산한다.
"""

from dataclasses import dataclass

# 내연기관 승용차 1km 주행당 평균 CO2 배출량(kg/km). 절감량 환산 상수.
CO2_KG_PER_KM = 0.103

# 나무 1그루가 1년간 흡수하는 CO2 양(kg). 절감량을 나무 그루 수로 환산할 때 사용.
TREE_ABSORB_KG_PER_YEAR = 6.6


@dataclass
class Co2Saving:
    saved_kg: float
    trees_equiv: float


def calculate_co2_saving(distance_km: float) -> Co2Saving:
    """주행거리(km)로부터 CO2 절감량과 나무 환산 그루 수를 계산한다."""
    distance = max(0.0, distance_km)
    saved_kg = round(distance * CO2_KG_PER_KM, 2)
    trees_equiv = round(saved_kg / TREE_ABSORB_KG_PER_YEAR, 2)
    return Co2Saving(saved_kg=saved_kg, trees_equiv=trees_equiv)
