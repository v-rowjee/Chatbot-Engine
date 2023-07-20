import re


class CleanSlot:

    @staticmethod
    def height(height):
        try:
            int(float(height))
            return height
        except ValueError:
            pass

        height = height.lower().replace(' ', '').replace(',', '').replace("'", 'foot').replace('"', 'inch').replace("ft",
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
                output = float(m_cm.group(1)) * 100
            if m_cm.group(2):
                output += float(m_cm.group(2)) * 100
            if m_cm.group(3):
                output += float(m_cm.group(3))
            return int(output)
        if cm:
            return int(float(cm.group(1)))

        if foot_inch:
            if foot_inch.group(1):
                output = float(foot_inch.group(1)) * 30.48
            if foot_inch.group(2):
                output += float(foot_inch.group(2)) * 2.54
            return int(output)
        if inch:
            return int(float(inch.group(1)))

    @staticmethod
    def weight(weight):
        try:
            int(float(weight))
            return weight
        except ValueError:
            pass
        weight = weight.lower().replace(' ', '').replace(',', '').replace("lb", "pound").replace("lbs", "pound").replace("pounds",
                                                                                                        "pound").replace(
            "kilo", "kg")
        kg = re.search(r"(\d+(\.\d+)?)(?:kg)", weight)
        pound = re.search(r"(\d+(\.\d+)?)(?:pound)", weight)
        if kg:
            return int(float(kg.group(1)))
        if pound:
            return int(float(pound.group(1) * 0.45359237))
        return None

    @staticmethod
    def age(age):
        try:
            int(float(age))
            return age
        except ValueError:
            pass

        years = re.search(r"(\d+)", age)
        if years:
            return int(float(years.group(1)))
        return None
