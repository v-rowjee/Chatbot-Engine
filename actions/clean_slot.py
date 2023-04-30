import re


class CleanSlot:

    @staticmethod
    def height(height):
        try:
            int(height)
            return height
        except ValueError:
            pass

        height = height.lower().replace(' ', '').replace("'", 'foot').replace('"', 'inch').replace("ft",
                                                                                                   "foot").replace(
            "feet", "foot").replace("inches", "inch").replace("inchs", "inch").replace("cms", "cm").replace(
            "centimeter", "cm").replace("meters", "m").replace("metre", "m")

        # Search for height in various units and convert to centimeters
        m_cm = re.search(r"(\d+)(\.\d+)?m(\d+)?(?:cm)?", height)
        cm = re.search(r"(\d+)cm", height)

        foot_inch = re.search(r"(\d+)foot(\d+)?(?:inch)?", height)
        inch = re.search(r"(\d+)inch", height)

        output = 0

        if m_cm:
            if m_cm.group(1):
                output = int(m_cm.group(1)) * 100
            if m_cm.group(2):
                output += int(m_cm.group(2)) * 100
            if m_cm.group(3):
                output += int(m_cm.group(3))
            return output
        if cm:
            return int(cm.group(1))

        if foot_inch:
            if foot_inch.group(1):
                output = int(foot_inch.group(1)) * 30.48
            if foot_inch.group(2):
                output += int(foot_inch.group(2)) * 2.54
            return output
        if inch:
            return int(inch.group(1))

    @staticmethod
    def weight(weight):
        try:
            int(weight)
            return weight
        except ValueError:
            pass
        weight = weight.lower().replace(' ', '').replace("lb", "pound").replace("lbs", "pound").replace("pounds",
                                                                                                        "pound").replace(
            "kilo", "kg")
        kg = re.search(r"(\d+(\.\d+)?)(?:kg)", weight)
        pound = re.search(r"(\d+(\.\d+)?)(?:pound)", weight)
        if kg:
            return int(kg.group(1))
        if pound:
            return int(pound.group(1)) * 0.45359237
        return None

    @staticmethod
    def age(age):
        try:
            int(age)
            return age
        except ValueError:
            pass

        years = re.search(r"\d+", age)
        if years:
            return int(years.group())
        return None
