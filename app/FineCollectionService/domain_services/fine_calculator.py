class FineCalculator:
    def calculate_fine(self, license_key: str, violation_in_kmh: int) -> int:
        if not license_key or not license_key.strip() \
                or license_key != "HX783-K2L7V-CRJ4A-5PN1G":
            raise ValueError("Invalid or no license key specified.")

        fine = 9  # default administration fee

        if violation_in_kmh < 5:
            fine += 18
        elif violation_in_kmh < 10:
            fine += 31
        elif violation_in_kmh < 15:
            fine += 64
        elif violation_in_kmh < 20:
            fine += 121
        elif violation_in_kmh < 25:
            fine += 174
        elif violation_in_kmh < 30:
            fine += 232
        elif violation_in_kmh < 35:
            fine += 297
        elif violation_in_kmh == 35:
            fine += 372
        else:
            # violation above 35 km/h will be determined by the prosecutor
            return 0

        return fine