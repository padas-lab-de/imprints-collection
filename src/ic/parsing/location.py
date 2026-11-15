from collections.abc import Sized
from typing import Any, Dict, List, Optional, Tuple


class LocationExtractor:
    """
    Extractor for addresses and geo coordinates specified in one of the following formats:
        'address': 'addressValue'
        'address': Dict[str, str] with dictionary keys contained in self.address_components (see __init__)
        'type': value in self.postal_string (see __init__), 'value': 'addressValue'
        'type': value in self.postal_string (see __init__), 'properties': Dict[str, str] with dictionary keys contained
        in self.address_components (see __init__)
        'geo': Dict[str, str] with keys 'longitude' and 'latitude'
        'geo': Dict[str, str] with key 'latitude', where the value of 'latitude' is a list of length 2
        'type': value in self.geo_coords (see __init__), 'properties': Dict[str, str] with same keys as detailed above
    """

    def __init__(self, schema_name: str = "address"):
        """
        Initializes the class with the schema name.

        :param schema_name: The name of the schema part used for extraction.
        """
        self.schema_name = schema_name

        self.address_components = [
            "addressLocality",
            "addressRegion",
            "addressCountry",
            "postalCode",
            "postOfficeBoxNumber",
            "streetAddress",
        ]
        self.postal_string = [
            "PostalAddress",
            "https://schema.org/PostalAddress",
            "http://schema.org/PostalAddress",
        ]
        self.geo_coords = [
            "GeoCoordinates",
            "https://schema.org/GeoCoordinates",
            "http://schema.org/GeoCoordinates",
        ]
        self.addresses = {}
        self.coords = {}
        self.found_address = {}
        self.found_geo = {}
        self.geo = "geo"
        self.longitude = "longitude"
        self.latitude = "latitude"

        self.property_string = "properties"
        self.value_string = "value"
        self.type_strings = ["type", "@type"]
        self.format = "format"
        self.formats = {}

    @staticmethod
    def _extract_address_item(address_dict: dict, address_item: str) -> Optional[str]:
        """
        Checks if the given address item is contained in the dictionary's keys and returns the corresponding value if
        it is a non-empty string.

        :param address_dict: The dictionary to check.
        :param address_item: The key to search for.
        :return: The extracted address part or None.
        """
        if address_item in address_dict.keys():
            extracted_item = address_dict[address_item]
            if isinstance(extracted_item, str) and extracted_item.strip():
                return extracted_item.strip()

    def _contains_address_information(self, address_dict: dict) -> bool:
        """
        Checks whether the given dictionary contains any address components specified by the PostalAddress schema.

        :param address_dict: The dictionary to check.
        :return: True if the dictionary contains any address components, else False.
        """
        for key in address_dict.keys():
            if (
                key in self.address_components
                and isinstance(address_dict[key], str)
                and address_dict[key].strip()
            ):
                return True
        return False

    def _get_type_string(self, schema_dict: dict) -> str:
        """
        Returns the value of the type string ('type' or '@type') if contained in the given dictionary.

        :param schema_dict: The dictionary to check.
        :return: The extracted type string or None.
        """
        type_string = ""
        for schema_type in self.type_strings:
            if schema_type in schema_dict.keys():
                type_string = schema_type
        return type_string

    def _is_type_dict(self, schema_dict: dict, type_value: list) -> bool:
        """
        Checks whether the given dictionary's keys contain a type string ('type' or '@type') and 'properties'.

        :param schema_dict: The dictionary to check.
        :return: True if the dictionary contains the corresponding keys, else False.
        """
        type_string = self._get_type_string(schema_dict)
        if type_string and self.property_string in schema_dict.keys():
            return schema_dict[type_string] in type_value and isinstance(
                schema_dict[self.property_string], dict
            )
        return False

    def _is_value_address(self, schema_dict: dict) -> bool:
        """
        Checks whether the given dictionary's keys contain a type string ('type' or '@type') and 'value'.

        :param schema_dict: The dictionary to check.
        :return: True if the dictionary contains the corresponding keys, else False.
        """
        type_string = self._get_type_string(schema_dict)
        if type_string and self.value_string in schema_dict.keys():
            return schema_dict[type_string] in self.postal_string and isinstance(
                schema_dict[self.value_string], str
            )
        return False

    def _extract_address_components(self, address_dict: dict) -> Dict[str, str]:
        """
        Extracts all PostalAddress components that can be found in the given dictionary and returns them as a list. If
        the dictionary does not contain a specific address component, an empty string is appended to the list.

        :param address_dict: The dictionary containing address components.
        :return: A list of extracted PostalAddress components.
        """
        components = {}
        for component in self.address_components:
            extracted = self._extract_address_item(address_dict, component)
            components[component] = extracted if extracted else ""
        return components

    def _extract_postal_address(self, address_dict: dict) -> Optional[Dict[str, str]]:
        """
        Checks whether the given dictionary contains any postal components specified by the PostalAddress schema and
        returns a list of the extracted values, if present.

        :param address_dict: The dictionary to check.
        :return: A list of extracted PostalAddress components or None.
        """
        if self._contains_address_information(address_dict):
            return self._extract_address_components(address_dict)

    def _extract_lon_lat(self, geo_coords: dict) -> Optional[Dict[str, str]]:
        """
        Extracts the latitude and longitude from the given geo coordinates, if present.

        :param geo_coords: The dictionary containing geo coordinates.
        :return: A dictionary containing the latitude and longitude.
        """
        if not self.latitude in geo_coords.keys():
            return None
        if self.longitude in geo_coords.keys():
            if geo_coords[self.longitude] and geo_coords[self.latitude]:
                return {
                    self.longitude: str(geo_coords[self.longitude]),
                    self.latitude: str(geo_coords[self.latitude]),
                }
        else:
            lat_lon_tuple = geo_coords[self.latitude]
            if not isinstance(lat_lon_tuple, Sized):
                return None

            if len(lat_lon_tuple) == 2:
                return {
                    self.longitude: lat_lon_tuple[1],
                    self.latitude: lat_lon_tuple[0],
                }
            else:
                return None

    def _extract_address(self, schema_entry: dict) -> Optional[dict | str]:
        """
        Extracts address information from the given schema entry, if present.

        :param schema_entry: The schema data that might contain address information.
        :return: The extracted address information or None.
        """
        if self.schema_name in schema_entry.keys() and isinstance(
            schema_entry[self.schema_name], str
        ):
            return schema_entry[self.schema_name]
        elif self.schema_name in schema_entry.keys() and isinstance(
            schema_entry[self.schema_name], dict
        ):
            return schema_entry[self.schema_name]
        elif self._is_type_dict(schema_entry, self.postal_string):
            return schema_entry[self.property_string]
        elif self._is_value_address(schema_entry):
            return schema_entry[self.value_string]

    def _extract_geo_coords(self, schema_entry: dict) -> Optional[dict]:
        """
        Extracts geo coordinates from the given schema entry, if present.

        :param schema_entry: The schema data that might contain geo information.
        :return: The extracted geo information or None.
        """
        if self.geo in schema_entry.keys() and isinstance(schema_entry[self.geo], dict):
            return schema_entry[self.geo]
        elif self._is_type_dict(schema_entry, self.geo_coords):
            return schema_entry[self.property_string]

    def extract_schema(
        self, schema_entry: dict
    ) -> Tuple[Optional[dict | str], Optional[dict]]:
        """
        Extracts geolocation data from the given schema entry, if present.

        :param schema_entry: The schema data that might contain address or geo information.
        :return: The extracted information or None.
        """
        address = self._extract_address(schema_entry)
        geo = self._extract_geo_coords(schema_entry)
        return address, geo

    def _get_schema_type_name(self, schema_dict: dict) -> str:
        """
        Returns the name of the current schema type if present in the dictionary, .i.e. the value of a 'type' or
        '@type' annotation.

        :param schema_dict: The dictionary to check.
        :return: The extracted type string or an empty string.
        """
        type_string = self._get_type_string(schema_dict)
        if (
            type_string
            and schema_dict[type_string]
            and isinstance(schema_dict[type_string], str)
        ):
            return schema_dict[type_string]
        return ""

    def extract_entry(self, schema_entry: dict):
        """
        Attempts to extract geolocation information from the given schema entry and adds it to the current address and
        geo coordinates lists.

        :param schema_entry: The schema data that might contain location information.
        :param data_format: The format of the data, i.e. Microdata or JSON-LD.
        :param record_id: The unique ID of the record.
        """
        type_string = self._get_schema_type_name(schema_entry)
        address_dict, geo_coords = self.extract_schema(schema_entry)

        address, coords = {}, {}
        if address_dict:
            if isinstance(address_dict, dict):
                address = self._extract_postal_address(address_dict)
                if address:
                    address["type"] = type_string
            if isinstance(address_dict, str) and address_dict.strip():
                address = {"type": type_string, "value": address_dict.strip()}
        if geo_coords:
            coords = self._extract_lon_lat(geo_coords)

        return address, coords


def process_extruct_result(
    json_ld: list, microdata: list, **kwargs
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    extractor = LocationExtractor()
    results_address, results_coords = [], []
    if json_ld:
        list_address, list_coords = traverse_schema_data(json_ld, extractor=extractor)
        results_address.extend(list_address)
        results_coords.extend(list_coords)
    if microdata:
        list_address, list_coords = traverse_schema_data(microdata, extractor=extractor)
        results_address.extend(list_address)
        results_coords.extend(list_coords)
    return results_address, results_coords


def _extract_nested_dict(schema_item: Any) -> Optional[list[dict]]:
    """
    Attempts to extract a dictionary potentially nested in the current data structure.

    :param schema_item: The item that might be or contain a dictionary.
    :return: An extracted dictionary, if present.
    """
    if isinstance(schema_item, dict):
        return [schema_item]
    elif isinstance(schema_item, list):
        dict_list = []
        for entry in schema_item:
            if isinstance(entry, dict):
                dict_list.append(entry)
        if len(dict_list) > 0:
            return dict_list


def _call_extraction_modules(
    extraction_module: LocationExtractor, data: Any
) -> Tuple[List[Any], List[Any]]:
    """
    Recursively applies all extraction modules to dictionaries representing parts of a microdata or json-ld string.

    :param extraction_module: The extraction module to apply.
    :param data: The data from which to extract.
    :param data_format: The format of the data, i.e. Microdata or JSON-LD.
    :param record_id: The unique ID of the record.
    """
    result_address = []
    result_coords = []
    if isinstance(data, dict):
        address, coords = extraction_module.extract_entry(data)
        result_address.append(address)
        result_coords.append(coords)
        for value in data.values():
            nested_dicts = _extract_nested_dict(value)
            if nested_dicts:
                for nested_dict in nested_dicts:
                    list_address, list_coords = _call_extraction_modules(
                        extraction_module, nested_dict
                    )
                    result_address.extend(list_address)
                    result_coords.extend(list_coords)
    elif isinstance(data, list):
        for _, entry in enumerate(data):
            list_address, list_coords = _call_extraction_modules(
                extraction_module, entry
            )
            result_address.extend(list_address)
            result_coords.extend(list_coords)
    return result_address, result_coords


def traverse_schema_data(
    data: list, extractor: LocationExtractor
) -> Tuple[List[Any], List[Any]]:
    """
    Iterates over the sequence entries containing parts of extracted microdata or JSON-LD and applies the extractors on
    it. Extracted data is then stored in the dictionary that is returned.

    :param data: The data to check.
    :param extractors: The extractors to apply.
    :param data_format: The format of the data, i.e. Microdata or JSON-LD.
    :param record_id: The unique ID of the record.
    :return: A dictionary containing the extracted data with one entry per extractor.
    """
    results_address = []
    results_coords = []

    for item in data:
        list_address, list_coords = _call_extraction_modules(extractor, item)
        results_address.extend(list_address)
        results_coords.extend(list_coords)

    return results_address, results_coords
