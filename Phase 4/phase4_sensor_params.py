
# Phase 4: SAR Sensor Parameters for Maritime Surveillance
# Based on typical maritime surveillance SAR characteristics

import csv
from dataclasses import dataclass

@dataclass
class SARSensorParams:
    '''SAR sensor parameters for maritime surveillance constellation.'''

    # Swath width in kilometers
    swath_width_km: float = 50  # Typical for maritime surveillance SAR

    # Elevation mask in degrees (minimum elevation angle)
    elevation_mask_deg: float = 10

    # Dwell time (integration time per pass) in seconds
    dwell_time_s: float = 60

    # Detection probability (simplified model)
    pd_nominal: float = 0.95  # High confidence detection on clear pass

    # Dark ship cross-section effective area (m²)
    # Smaller vessels have lower RCS
    dark_ship_rcs_m2: float = 50  # Conservative estimate for small vessel

    # SAR processing delay (from sensor to detection report)
    sar_processing_delay_s: float = 30

    # Mode definitions
    modes = {
        'PATROL': {
            'coverage_type': 'wide_area',
            'description': 'Wide-swath patrol over entire EEZ',
            'swath_factor': 1.0,  # Use full swath
            'detection_prob': 0.95,
            'data_volume_per_pass_gb': 2.0,
        },
        'TRACKING': {
            'coverage_type': 'focused',
            'description': 'Focused tracking along known ship routes',
            'swath_factor': 0.5,  # Narrower beam for precise targeting
            'detection_prob': 0.99,  # Higher confidence on tracked routes
            'data_volume_per_pass_gb': 0.8,
        }
    }

    def get_effective_swath(self, mode: str) -> float:
        '''Get effective swath width for given mode.'''
        if mode not in self.modes:
            raise ValueError(f"Unknown mode: {mode}")
        factor = self.modes[mode]['swath_factor']
        return self.swath_width_km * factor

    def get_detection_prob(self, mode: str) -> float:
        '''Get detection probability for given mode.'''
        if mode not in self.modes:
            raise ValueError(f"Unknown mode: {mode}")
        return self.modes[mode]['detection_prob']

# Default sensor configuration
DEFAULT_SENSOR = SARSensorParams()

# Typical ship routes in Indian EEZ (simplified for Phase 4 PoC)
# These represent likely shipping lanes and transits
SHIP_ROUTES = {
    'EEZ_West': {
        # Shipping lanes in Arabian Sea EEZ
        'primary_routes': [
            {
                'route_id': 'Route_W1',
                'latitude_band': (10.0, 14.0),  # Latitude range
                'description': 'Gujarat coast shipping lane'
            },
            {
                'route_id': 'Route_W2',
                'latitude_band': (14.0, 18.0),
                'description': 'Maharashtra coast shipping lane'
            },
        ]
    },
    'EEZ_East': {
        # Shipping lanes in Bay of Bengal EEZ
        'primary_routes': [
            {
                'route_id': 'Route_E1',
                'latitude_band': (10.0, 15.0),
                'description': 'Andhra-Odisha coast shipping lane'
            },
            {
                'route_id': 'Route_E2',
                'latitude_band': (15.0, 20.0),
                'description': 'Eastern coast shipping lane'
            },
        ]
    }
}

if __name__ == '__main__':
    sensor = DEFAULT_SENSOR
    print("SAR Sensor Configuration:")
    print(f"  Swath Width: {sensor.swath_width_km} km")
    print(f"  Elevation Mask: {sensor.elevation_mask_deg}°")
    print(f"  Dwell Time: {sensor.dwell_time_s} s")
    print()
    print("Tasking Modes:")
    for mode, params in sensor.modes.items():
        print(f"  {mode}: {params['description']}")
        print(f"    Effective Swath: {sensor.get_effective_swath(mode)} km")
        print(f"    Detection Prob: {sensor.get_detection_prob(mode):.1%}")
        print()
