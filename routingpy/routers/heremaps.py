# -*- coding: utf-8 -*-
# Copyright (C) 2019 GIS OPS UG
#
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#

from .base import Router, DEFAULT
from routingpy import convert
from routingpy.direction import Direction, Directions
from routingpy.isochrone import Isochrones, Isochrone
from routingpy.matrix import Matrix


class HereMaps(Router):
    """Performs requests to the HERE Maps API services."""

    _DEFAULT_BASE_URL = 'https://route.api.here.com/routing/7.2'

    def __init__(self,
                 app_id=None,
                 app_code=None,
                 user_agent=None,
                 timeout=DEFAULT,
                 retry_timeout=None,
                 requests_kwargs=None,
                 retry_over_query_limit=False):
        """
        Initializes a HERE Maps client.

        :param app_id: HERE Maps app id. 
        :type app_id: str

        :param app_code: HERE Maps app code.
        :type app_code: str

        :param user_agent: User-Agent to send with the requests to routing API.
            Overrides ``options.default_user_agent``.
        :type user_agent: str

        :param timeout: Combined connect and read timeout for HTTP requests, in
            seconds. Specify "None" for no timeout.
        :type timeout: int

        :param retry_timeout: Timeout across multiple retriable requests, in
            seconds.
        :type retry_timeout: int

        :param requests_kwargs: Extra keyword arguments for the requests
            library, which among other things allow for proxy auth to be
            implemented. See the official requests docs for more info:
            http://docs.python-requests.org/en/latest/api/#main-interface
        :type requests_kwargs: dict

        :param retry_over_query_limit: If True, the client will retry when query
            limit is reached (HTTP 429). Default False.
        :type retry_over_query_limit: bool
        """

        if app_id is None and app_code is None:
            raise KeyError("HERE Maps app_id and app_code must be specified.")

        self.app_code = app_code
        self.app_id = app_id

        super(HereMaps, self).__init__(self._DEFAULT_BASE_URL, user_agent,
                                       timeout, retry_timeout, requests_kwargs,
                                       retry_over_query_limit)

    class WayPoint(object):
        """
        Optionally construct a waypoint from this class with additional attributes.
        """

        def __init__(self,
                     position,
                     waypoint_type=None,
                     stopover_duration=None,
                     transit_radius='',
                     user_label='',
                     heading=''):
            """
            Constructs a waypoint with additional information.
            https://developer.here.com/documentation/routing/topics/resource-param-type-waypoint.html

            :param position: Indicates that the parameter contains a geographical position.
            :type position: list

            :param waypoint_type: 180 degree turns are allowed for stopOver but not for passThrough.
                Waypoints defined through a drag-n-drop action should be marked as pass-through. 
                PassThrough waypoints will not appear in the list of maneuvers.
            :type waypoint_type: str

            :param stopover_duration: Stopover delay in seconds. 
                Impacts time-aware calculations. Ignored for passThrough.
            :type stopover_duration: int

            :param transit_radius: Matching Links are selected within the 
                specified TransitRadius, in meters. 
                For example to drive past a city without necessarily going into the 
                city center you can specify the coordinates of the center and a 
                TransitRadius of 5000m.
            :type transit_radius: int

            :param user_label: Custom label identifying this waypoint.
            :type user_label: str

            :param heading: Heading in degrees starting at true north and continuing 
                clockwise around the compass. 
                North is 0 degrees, East is 90 degrees, South is 180 degrees, 
                and West is 270 degrees.
            :type heading: int
            """

            self.position = position
            self.waypoint_type = waypoint_type
            self.stopover_duration = stopover_duration
            self.transit_radius = str(transit_radius)
            self.user_label = user_label
            self.heading = str(heading)

        def make_waypoint(self):

            here_waypoint = ['geo']
            if self.waypoint_type is not None and self.stopover_duration is not None:
                here_waypoint.append(
                    convert._delimit_list(
                        [self.waypoint_type, self.stopover_duration], ','))
            elif self.waypoint_type is not None:
                here_waypoint.append(self.waypoint_type)

            position = convert._delimit_list(
                [convert._format_float(f) for f in self.position], ',')
            position += ';' + self.transit_radius
            position += ';' + self.user_label
            position += ';' + self.heading
            here_waypoint.append(position)
            return convert._delimit_list(here_waypoint, '!')

    class RoutingMode(object):
        """
        Optionally construct the routing mode from this class with additional attributes.
        """

        def __init__(self,
                     mode_type='fastest',
                     mode_transport_type='car',
                     mode_traffic=None,
                     features=None):
            """
            https://developer.here.com/documentation/routing/topics/resource-param-type-routing-mode.html

            :param mode_type: RoutingType relevant to calculation.
            :type mode_type: str

            :param mode_transport_type: Specify which mode of transport to calculate the route for.
            :type mode_transport_type: str

            :param mode_traffic: Specify whether to optimize a route for traffic.
            :type mode_traffic: bool

            :param features: Route feature weightings to be applied when calculating 
                the route. As many as required.
            :type features: dict
            """

            self.mode_type = mode_type
            self.mode_transport_type = mode_transport_type
            self.mode_traffic = mode_traffic
            if features is not None:
                self.features = features

        def make_routing_mode(self):

            routing_mode = []
            routing_mode.append(self.mode_type)
            routing_mode.append(self.mode_transport_type)

            if self.mode_traffic is not None:
                routing_mode.append('traffic:' + self.mode_traffic)

            if self.features is not None:
                get_features = []
                for f, w in self.features.items():
                    get_features.append(
                        convert._delimit_list([f, str(w)], ':'))
                routing_mode.append(convert._delimit_list(get_features, ','))
            return convert._delimit_list(routing_mode, ';')

    def directions(self,
                   coordinates,
                   profile,
                   format='json',
                   request_id=None,
                   avoid_areas=None,
                   avoid_links=None,
                   avoid_seasonal_closures=None,
                   avoid_turns=None,
                   allowed_zones=None,
                   exclude_zones=None,
                   exclude_zone_types=None,
                   exclude_countries=None,
                   arrival=None,
                   departure=None,
                   alternatives=None,
                   metric_system=None,
                   view_bounds=None,
                   resolution=None,
                   instruction_format=None,
                   language=None,
                   json_attributes=None,
                   json_callback=None,
                   representation=None,
                   route_attributes=[
                       'waypoints', 'summary', 'shape', 'boundingBox', 'legs'
                   ],
                   leg_attributes=None,
                   maneuver_attributes=None,
                   link_attributes=None,
                   line_attributes=None,
                   generalization_tolerances=None,
                   vehicle_type=None,
                   license_plate=None,
                   max_number_of_changes=None,
                   avoid_transport_types=None,
                   walk_time_multiplier=None,
                   walk_speed=None,
                   walk_radius=None,
                   combine_change=None,
                   truck_type=None,
                   trailers_count=None,
                   shipped_hazardous_goods=None,
                   limited_weight=None,
                   weight_per_axle=None,
                   height=None,
                   width=None,
                   length=None,
                   tunnel_category=None,
                   truck_restriction_penalty=None,
                   return_elevation=None,
                   consumption_model=None,
                   custom_consumption_details=None,
                   speed_profile=None,
                   dry_run=None):
        """Get directions between an origin point and a destination point.

        For more information, https://developer.here.com/documentation/routing/topics/resource-calculate-route.html.

        :param coordinates: The coordinates tuple the route should be calculated
            from in order of visit. Can be a list/tuple of [lon, lat] or :class:`HereMaps.WayPoint` instance or a
            combination of those. For further explanation, see
            https://developer.here.com/documentation/routing/topics/resource-param-type-waypoint.html
        :type coordinates: list of list or list of :class:`HereMaps.WayPoint`

        :param profile: Specifies the routing mode of transport and further options.
            Can be a str or :class:`HereMaps.RoutingMode`
            https://developer.here.com/documentation/routing/topics/resource-param-type-routing-mode.html
        :type profile: str or :class:`HereMaps.RoutingMode`

        :param format: Currently only "json" supported. 
        :type format: str

        :param request_id: Clients may pass in an arbitrary string to trace request 
            processing through the system. The RequestId is mirrored in the MetaInfo 
            element of the response structure.
        :type request_id: str

        :param avoid_areas: Areas which the route must not cross. Array of BoundingBox. 
            Example with 2 bounding boxes
            https://developer.here.com/documentation/routing/topics/resource-param-type-bounding-box.html
        :type avoid_areas: list of list of list

        :param avoid_links: Links which the route must not cross. The list of LinkIdTypes.
        :type avoid_areas: list of str

        :param avoid_seasonal_closures: The optional avoid seasonal closures boolean 
            flag can be specified to avoid usage of seasonally closed links.
            Examples of seasonally closed links are roads that may be closed during the 
            winter due to weather conditions or ferries that may be out of operation 
            for the season (based on past closure dates).
        :type avoid_seasonal_closures: bool

        :param avoid_turns: List of turn types that the route should avoid. 
            Defaults to empty list. 
            https://developer.here.com/documentation/routing/topics/resource-type-enumerations.html
        :type avoid_turns: str

        :param allowed_zones: Identifiers of zones where routing engine should 
            not take zone restrictions into account (for example in case of a 
            special permission to access a restricted environmental zone).
            https://developer.here.com/documentation/routing/topics/resource-get-routing-zones.html
        :type allowed_zones: list of int

        :param exclude_zones: Identifiers of zones which the route must not cross 
            under any circumstances.
            https://developer.here.com/documentation/routing/topics/resource-get-routing-zones.html
        :type exclude_zones: list of int

        :param exclude_zone_types: List of zone types which the route must not 
            cross under any circumstances.
            https://developer.here.com/documentation/routing/topics/resource-type-enumerations.html
            #resource-type-enumerations__enum-routing-zone-type-type
        :type exclude_zone_types: list of str

        :param exclude_countries: Countries that must be excluded from route calculation.
        :type exclude_zone_types: list of str

        :param departure: Time when travel is expected to start. Traffic speed and 
            incidents are taken into account
            when calculating the route (note that in case of a past
            departure time the historical traffic is limited to one year).  
            You can use now to specify the current time. Specify either departure 
            or arrival, not both. When the optional timezone offset is not 
            specified, the time is assumed to be the local.
            Formatted as iso time, e.g. 2018-07-04T17:00:00+02.
        :type departure: str

        :param arrival: Time when travel is expected to end. Specify either 
            departure or arrival, not both.
            When the optional timezone offset is not specified, the time is assumed to be the local.
            Formatted as iso time, e.g. 2018-07-04T17:00:00+02.
        :type arrival: str        

        :param alternatives: Maximum number of alternative routes that will be 
            calculated and returned. Alternative routes can be unavailable, thus 
            they are not guaranteed to be returned. If at least one via point is used
            in a route request, returning alternative routes is not supported. 
            0 stands for "no alternative routes", i.e. only best route is returned.
        :type alternatives: int

        :param metric_system: Defines the measurement system used in instruction text. 
            When imperial is selected, units used are based on the language specified 
            in the request. Defaults to metric when not specified.
        :type metric_system: str

        :param view_bounds: If the view bounds are given in the request then only 
            route shape points which fit into these bounds will be returned. 
            The route shape beyond the view bounds is reduced to the points which
            are referenced by links, legs or maneuvers.
        :type view_bounds: list or tuple

        :param resolution: Specifies the resolution of the view and a possible snap 
            resolution in meters per pixel in the response. You must specify a whole, positive integer.
            If you specify only one value, then this value defines the view resolution only.
            You can use snap resolution to adjust waypoint links to the resolution of the client display.
            e.g. {'viewresolution': 300,'snapresolution': 300}
        :type resolution: dict

        :param instruction_format: Defines the representation format of the maneuver's instruction text. Html or txt.
        :type instruction_format: str

        :param language: A list of languages for all textual information, 
            the first supported language is used. If there are no matching supported 
            languages the response is an error. Defaults to en-us.
            https://developer.here.com/documentation/routing/topics/resource-param-type-languages.html#languages
        :type language: str

        :param json_attributes: Flag to control JSON output. Combine parameters 
            by adding their values. 
            https://developer.here.com/documentation/routing/topics/resource-param-type-json-representation.html
        :type json_attributes: int

        :param json_callback: Name of a user-defined function used to wrap the JSON response.
        :type json_callback: str

        :param representation: Define which elements are included in the response 
            as part of the data representation
            of the route.
            https://developer.here.com/documentation/routing/topics/resource-param-type-route-representation-options.html#type-route-represenation-mode
        :type representation: list of str

        :param route_attributes: Define which attributes are included in the 
            response as part of the data representation of the route. Defaults to 
            waypoints, summary, legs and additionally lines if publicTransport or
            publicTransportTimeTable mode is used.
            https://developer.here.com/documentation/routing/topics/resource-param-type-route-representation-options.html#type-route-attribute
        :type route_attributes: list of str

        :param leg_attributes: Define which attributes are included in the response 
            as part of the data representation
            of the route legs. Defaults to maneuvers, waypoint, length, travelTime.
            https://developer.here.com/documentation/routing/topics/resource-param-type-route-representation-options.html#type-route-leg-attribute
        :type leg_attributes: list of str

        :param maneuver_attributes: Define which attributes are included in the 
            response as part of the data
            representation of the route maneuvers. Defaults to position, length, travelTime.
            https://developer.here.com/documentation/routing/topics/resource-param-type-route-representation-options.html#type-maneuver-attribute
        :type maneuver_attributes: list of str

        :param link_attributes: Define which attributes are included in the response 
            as part of the data representation of the route links. Defaults to shape, speedLimit.
            https://developer.here.com/documentation/routing/topics/resource-param-type-route-representation-options.html#type-route-link-attribute
        :type link_attributes: list of str

        :param line_attributes: Sequence of attribute keys of the fields that are 
            included in public transport line elements. If not specified, 
            defaults to lineForeground, lineBackground.
            https://developer.here.com/documentation/routing/topics/resource-param-type-route-representation-options.html#type-public-transport-line-attribute
        :type line_attributes: list of str

        :param generalization_tolerances: Specifies the desired tolerances for 
            generalizations of the base route geometry. Tolerances are given in 
            degrees of longitude or latitude on a spherical approximation of the Earth.
            One meter is approximately equal to 0:00001 degrees at typical latitudes.
        :type generalization_tolerances: list of float

        :param param vehicle_type: Specifies type of vehicle engine and average 
            fuel consumption, which can be used to estimate CO2 emission for
            the route summary.
            https://developer.here.com/documentation/routing/topics/resource-param-type-vehicle-type.html
        :type vehicle_type: str

        :param param license_plate: Specifies fragments of vehicle's license plate number. 
            The lastcharacter is currently the only supported fragment type. 
            The license plate parameter enables evaluation of license plate
            based vehicle restrictions like odd/even scheme in Indonesia.
        :type license_plate: str

        :param max_number_of_changes: Restricts number of changes in a public 
            transport route to a given value. The parameter does not filter resulting 
            alternatives. Instead, it affects route calculation so that only
            routes containing at most the given number of changes are considered. 
            The provided value must be between 0 and 10.
        :type max_number_of_changes: int

        :param avoid_transport_types: Public transport types that shall not be included 
            in the response route. Please refer to Enumeration Types for a list of supported values.
            https://developer.here.com/documentation/routing/topics/resource-type-enumerations.html
        :type avoid_transport_types: list of str 

        :param walk_time_multiplier: Allows to prefer or avoid public transport 
            routes with longer walking distances. A value > 1.0 means a slower 
            walking speed and will prefer routes with less walking distance.
            The provided value must be between 0.01 and 100.
        :type walk_time_multiplier: float

        :param walk_speed: Specifies speed which will be used by a service as a 
            walking speed for pedestrian routing (meters per second). 
            This parameter affects pedestrian, publicTransport and publicTransportTimetable modes.
            The provided value must be between 0.5 and 2.
        :type walk_speed: float

        :param walk_radius: Allows the user to specify a maximum distance to the 
            start and end stations of a public transit route. Only valid for 
            publicTransport and publicTransportTimetable routes.
            The provided value must be between 0 and 6000.
        :type walk_radius: int

        :param combine_change: Enables the change maneuver in the route response, 
            which indicates a public transit line change. In the absence of this 
            maneuver, each line change is represented with a pair of subsequent enter
            and leave maneuvers. We recommend enabling combineChange behavior wherever 
            possible, to simplify client-side development.
        :type combine_change: bool

        :param truck_type: Truck routing only, specifies the vehicle type. Defaults to truck.
        :type truck_type: str

        :param trailers_count: Truck routing only, specifies number of trailers 
            pulled by a vehicle. The provided value must be between 0 and 4. 
            Defaults to 0.
        :type trailers_count: int

        :param shipped_hazardous_goods: Truck routing only, list of hazardous 
            materials in the vehicle. Please refer to the enumeration type 
            HazardousGoodTypeType for available values. 
            Note the value allhazardousGoods does not apply to the request parameter.
            https://developer.here.com/documentation/routing/topics/resource-type-enumerations.html#resource-type-enumerations__enum-hazardous-good-type-type
        :type shipped_hazardous_goods: list of str

        :param limited_weight: Truck routing only, vehicle weight including 
            trailers and shipped goods, in tons. The provided value must be between 0 and 1000.
        :type limited_weight: int

        :param weight_per_axle: Truck routing only, vehicle weight per axle in 
            tons. The provided value must be between 0 and 1000.
        :type limited_weight: int

        :param height: Truck routing only, vehicle height in meters.
            The provided value must be between 0 and 50.
        :type height: int

        :param width: Truck routing only, vehicle width in meters. 
            The provided value must be between 0 and 50.
        :type width: int  

        :param length: Truck routing only, vehicle length in meters.
            The provided value must be between 0 and 300.
        :type length: int        

        :param tunnel_category: Truck routing only, specifies the tunnel category 
            to restrict certain route links. The route will pass only through tunnels 
            of a less strict category.
        :type tunnel_category: list of str

        :param truck_restriction_penalty: Truck routing only, specifies the 
            penalty type on violated truck restrictions. Defaults to strict. 
            Refer to the enumeration type TruckRestrictionPenaltyType for 
            details on available values. 
            https://developer.here.com/documentation/routing/topics/resource-type-enumerations.html#resource-type-enumerations__enum-truck-restriction-penalty-type
        :type truck_restriction_penalty: str

        :param return_elevation: If set to true, all shapes inside routing response
            will consist of 3 values instead of 2. Third value will be elevation. 
            If there are no elevation data available for given shape point, 
            elevation will be interpolated from surrounding points. In case 
            there is no elevation data available for any of the shape points, 
            elevation will be 0.0. If jsonattributes=32, elevation cannot be returned.
        :type return_elevation: bool

        :param consumption_model: If you request information on consumption, 
            you must provide a consumption model. The possible values are default 
            and standard. When you specify the value standard, you must provide 
            additional information in the query parameter customconsumptiondetails
        :type consumption_model: str

        :param custom_consumption_details: Provides vehicle specific information 
            for use in the consumption model. This information can include such 
            things as the amount of energy consumed while travelling at a given speed.
            https://developer.here.com/documentation/routing/topics/resource-param-type-custom-consumption-details.html#type-standard
        :type custom_consumption_details: str

        :param speed_profile: Specifies the speed profile variant for a given routing mode. 
            The speed profile affects travel time estimation as well as roads evaluation 
            when computing the fastest route. Note that computed routes might differ depending on a used profile.
            https://developer.here.com/documentation/routing/topics/resource-param-type-speed-profile-type.html
        :type speed_profile: str

        :param dry_run: Print URL and parameters without sending the request.
        :param dry_run: bool

        :returns: One or multiple route(s) from provided coordinates and restrictions.
        :rtype: :class:`routingpy.direction.Direction` or :class:`routingpy.direction.Directions`

        """

        self.base_url = 'https://route.api.here.com/routing/7.2'
        params = {}

        params["app_code"] = self.app_code
        params["app_id"] = self.app_id

        for idx, wp in enumerate(coordinates):
            wp_index = "waypoint" + str(idx)
            if isinstance(wp, self.WayPoint):
                params[wp_index] = wp.make_waypoint()
            elif isinstance(wp, (list, tuple)):
                wp = 'geo!' + convert._delimit_list(
                    [convert._format_float(f) for f in wp], ',')
                params[wp_index] = wp

        if isinstance(profile, str):
            params["mode"] = profile
        elif isinstance(profile, self.RoutingMode):
            params["mode"] = profile.make_routing_mode()

        if request_id is not None:
            params["requestId"] = request_id

        if avoid_areas is not None:
            params["avoidAreas"] = convert._delimit_list([
                convert._delimit_list([
                    convert._delimit_list(
                        [convert._format_float(f) for f in pair], ',')
                    for pair in bounding_box
                ], ';') for bounding_box in avoid_areas
            ], '!')

        if avoid_links is not None:
            params["avoidLinks"] = convert._delimit_list(avoid_links, ',')

        if avoid_seasonal_closures is not None:
            params["avoidSeasonalClosures"] = convert._convert_bool(
                avoid_seasonal_closures)

        if avoid_turns is not None:
            params["avoidTurns"] = avoid_turns

        if allowed_zones is not None:
            params["allowedZones"] = convert._delimit_list(allowed_zones, ',')

        if exclude_zones is not None:
            params["excludeZones"] = convert._delimit_list(exclude_zones, ',')

        if exclude_zone_types is not None:
            params["excludeZoneTypes"] = convert._delimit_list(
                exclude_zone_types, ',')

        if exclude_countries is not None:
            params["excludeCountries"] = convert._delimit_list(
                exclude_countries, ',')

        if departure is not None:
            params["departure"] = departure
        elif arrival is not None:
            params["arrival"] = arrival

        if alternatives is not None:
            params["alternatives"] = alternatives

        if metric_system is not None:
            params["metricSystem"] = metric_system

        if view_bounds is not None:
            params["viewBounds"] = convert._delimit_list([
                convert._delimit_list([convert._format_float(f)
                                       for f in pair], ',')
                for pair in view_bounds
            ], ';')

        if resolution is not None:
            params["resolution"] = str(resolution['viewresolution'])
            if 'snapresolution' in resolution:
                params["resolution"] += ':' + str(resolution['snapresolution'])

        if instruction_format is not None:
            params["instructionFormat"] = instruction_format

        if json_attributes is not None:
            params["jsonAttributes"] = json_attributes

        if json_callback is not None:
            params["jsonCallback"] = json_callback

        if representation is not None:
            params["representation"] = convert._delimit_list(
                representation, ',')

        if route_attributes is not None:
            params["routeAttributes"] = convert._delimit_list(
                route_attributes, ',')

        if leg_attributes is not None:
            params["legAttributes"] = convert._delimit_list(
                leg_attributes, ',')

        if maneuver_attributes is not None:
            params["maneuverAttributes"] = convert._delimit_list(
                maneuver_attributes, ',')

        if link_attributes is not None:
            params["linkAttributes"] = convert._delimit_list(
                link_attributes, ',')

        if line_attributes is not None:
            params["lineAttributes"] = convert._delimit_list(
                line_attributes, ',')

        if generalization_tolerances is not None:
            params["generalizationTolerances"] = convert._delimit_list(
                generalization_tolerances, ',')

        if vehicle_type is not None:
            params["vehicleType"] = vehicle_type

        if license_plate is not None:
            params["licensePlate"] = license_plate

        if max_number_of_changes is not None:
            params["maxNumberOfChanges"] = max_number_of_changes

        if avoid_transport_types is not None:
            params["avoidTransportTypes"] = convert._delimit_list(
                avoid_transport_types, ',')

        if walk_time_multiplier is not None:
            params["walkTimeMultiplier"] = walk_time_multiplier

        if walk_speed is not None:
            params["walkSpeed"] = walk_speed

        if walk_radius is not None:
            params["walkRadius"] = walk_radius

        if combine_change is not None:
            params["combineChange"] = convert._convert_bool(combine_change)

        if truck_type is not None:
            params["truckType"] = truck_type

        if trailers_count is not None:
            params["trailersCount"] = trailers_count

        if shipped_hazardous_goods is not None:
            params["shippedHazardousGoods"] = convert._delimit_list(
                shipped_hazardous_goods, ',')

        if limited_weight is not None:
            params["limitedWeight"] = limited_weight

        if weight_per_axle is not None:
            params["weightPerAxle"] = weight_per_axle

        if height is not None:
            params["height"] = height

        if width is not None:
            params["width"] = width

        if length is not None:
            params["length"] = length

        if tunnel_category is not None:
            params["tunnelCategory"] = convert._delimit_list(
                tunnel_category, ',')

        if truck_restriction_penalty is not None:
            params["truckRestrictionPenalty"] = truck_restriction_penalty

        if return_elevation is not None:
            params["returnElevation"] = convert._convert_bool(return_elevation)

        if consumption_model is not None:
            params["consumptionModel"] = consumption_model

        if custom_consumption_details is not None:
            params["customConsumptionDetails"] = custom_consumption_details

        if speed_profile is not None:
            params["speedProfile"] = speed_profile

        return self._parse_direction_json(
            self._request(
                convert._delimit_list(["/calculateroute", format], '.'),
                get_params=params,
                dry_run=dry_run),
            alternatives=alternatives)

    @staticmethod
    def _parse_direction_json(response, alternatives):
        if response is None:
            return None

        if alternatives is not None and alternatives > 1:
            routes = []
            for route in response['response']['route']:
                routes.append(
                    Direction(route['shape'], route['summary']['baseTime'],
                              route['summary']['distance']))

            return Directions(directions=routes, raw=response)

        else:
            geometry = response['response']['route'][0].get('shape')
            duration = int(
                response['response']['route'][0]['summary'].get('baseTime'))
            distance = int(
                response['response']['route'][0]['summary'].get('distance'))

            return Direction(
                geometry=geometry,
                duration=duration,
                distance=distance,
                raw=response)

    def isochrones(self,
                   coordinates,
                   profile,
                   intervals,
                   interval_type,
                   format='json',
                   center_type='start',
                   request_id=None,
                   arrival=None,
                   departure=None,
                   single_component=None,
                   resolution=None,
                   max_points=None,
                   quality=None,
                   json_attributes=None,
                   json_callback=None,
                   truck_type=None,
                   trailers_count=None,
                   shipped_hazardous_goods=None,
                   limited_weight=None,
                   weight_per_axle=None,
                   height=None,
                   width=None,
                   length=None,
                   tunnel_category=None,
                   consumption_model=None,
                   custom_consumption_details=None,
                   speed_profile=None,
                   dry_run=None):
        """Gets isochrones or equidistants for a range of time/distance values around a given set of coordinates.

        For more information, https://developer.here.com/documentation/routing/topics/resource-calculate-isoline.html.

        :param coordinates: One pair of lng/lat values.
        :type coordinates: list of float

        :param profile: Specifies the routing mode of transport and further options.
            Can be a str or :class:`HereMaps.RoutingMode`
            https://developer.here.com/documentation/routing/topics/resource-param-type-routing-mode.html
        :type profile: str or :class:`HereMaps.RoutingMode`

        :param intervals: Range of isoline. Several comma separated values can be specified. 
            The unit is defined by parameter rangetype.
        :type ranges: list of int

        :param interval_type: Specifies type of range. Possible values are distance, 
            time, consumption. For distance the unit is meters. For time the unit is seconds. 
            For consumption it is defined by consumption model
        :type range_type: str

        :param format: Currently only "json" supported. 
        :type format: str

        :param center_type: If 'start' then the isoline will cover all roads which 
            can be reached from this point within given range.
            It cannot be used in combination with destination parameter. 
            If 'destination' Center of the isoline request. Isoline will cover all 
            roads from which this point can be reached within given range. 
            It cannot be used in combination with start parameter. 
        :type center_type: str

        :param departure: Time when travel is expected to start. Traffic speed and 
            incidents are taken into account
            when calculating the route (note that in case of a past
            departure time the historical traffic is limited to one year).  
            You can use now to specify the current time. Specify either departure 
            or arrival, not both. When the optional timezone offset is not 
            specified, the time is assumed to be the local.
            Formatted as iso time, e.g. 2018-07-04T17:00:00+02.
        :type departure: str

        :param arrival: Time when travel is expected to end. Specify either 
            departure or arrival, not both.
            When the optional timezone offset is not specified, the time is 
            assumed to be the local.
            Formatted as iso time, e.g. 2018-07-04T17:00:00+02.
        :type arrival: str        

        :param single_component: If set to true the isoline service will always 
            return single polygon, instead of creating a separate polygon 
            for each ferry separated island. Default value is false.
        :type single_component: bool

        :param resolution: Allows to specify level of detail needed for the
            isoline polygon. Unit is meters per pixel. Higher resolution may 
            cause increased response time from the service.
        :type resolution: int

        :param max_points: Allows to limit amount of points in the returned 
            isoline. If isoline consists of multiple components, sum of points from 
            all components is considered. Each component will have at least 2 points, 
            so it is possible that more points than maxpoints value will be returned. 
            This is in case when 2 * number of components is higher than maxpoints. 
            Enlarging number of maxpoints may cause increased response time from the service.
        :type max_points: int

        :param quality: Allows to reduce the quality of the isoline in favor 
            of the response time. Allowed values are 1, 2, 3. 
            Default value is 1 and it is the best quality.
        :type quality: int

        :param json_attributes: Flag to control JSON output. 
            Combine parameters by adding their values. 
            https://developer.here.com/documentation/routing/topics/resource-param-type-json-representation.html
        :type json_attributes: int

        :param truck_type: Truck routing only, specifies the vehicle type. Defaults to truck.
        :type truck_type: str

        :param trailers_count: Truck routing only, specifies number of trailers 
            pulled by a vehicle. The provided value must be between 0 and 4. Defaults to 0.
        :type trailers_count: int

        :param shipped_hazardous_goods: Truck routing only, list of hazardous 
            materials in the vehicle. Please refer to the enumeration type 
            HazardousGoodTypeType for available values. 
            Note the value allhazardousGoods does not apply to the request parameter.
            https://developer.here.com/documentation/routing/topics/resource-type-enumerations.html#resource-type-enumerations__enum-hazardous-good-type-type
        :type shipped_hazardous_goods: list of str

        :param limited_weight: Truck routing only, vehicle weight including 
            trailers and shipped goods, in tons. The provided value must be between 0 and 1000.
        :type limited_weight: int

        :param weight_per_axle: Truck routing only, vehicle weight per axle in tons. 
            The provided value must be between 0 and 1000.
        :type limited_weight: int

        :param height: Truck routing only, vehicle height in meters. 
            The provided value must be between 0 and 50.
        :type height: int

        :param width: Truck routing only, vehicle width in meters. 
            The provided value must be between 0 and 50.
        :type width: int  

        :param length: Truck routing only, vehicle length in meters. 
            The provided value must be between 0 and 300.
        :type length: int        

        :param tunnel_category: Truck routing only, specifies the tunnel category to 
            restrict certain route links. The route will pass only through tunnels of a less strict category.
        :type tunnel_category: list of str

        :param consumption_model: If you request information on consumption, you must 
            provide a consumption model. The possible values are default and standard. 
            When you specify the value standard, you must provide additional 
            information in the query parameter customconsumptiondetails
        :type consumption_model: str

        :param custom_consumption_details: Provides vehicle specific information 
            for use in the consumption model. This information can include such 
            things as the amount of energy consumed while travelling at a given speed.
            https://developer.here.com/documentation/routing/topics/resource-param-type-custom-consumption-details.html#type-standard
        :type custom_consumption_details: str

        :param speed_profile: Specifies the speed profile variant for a given 
            routing mode. The speed profile affects travel time estimation as 
            well as roads evaluation when computing the fastest route. 
            Note that computed routes might differ depending on a used profile.
            https://developer.here.com/documentation/routing/topics/resource-param-type-speed-profile-type.html
        :type speed_profile: str

        :param dry_run: Print URL and parameters without sending the request.
        :param dry_run: bool

        :returns: raw JSON response
        :rtype: dict
        """

        self.base_url = 'https://isoline.route.api.here.com/routing/7.2'
        params = {}

        params["app_code"] = self.app_code
        params["app_id"] = self.app_id

        if isinstance(coordinates, self.WayPoint):
            params[center_type] = coordinates.make_waypoint()
        elif isinstance(coordinates, (list, tuple)):
            params[center_type] = 'geo!' + convert._delimit_list(
                [convert._format_float(f) for f in coordinates], ',')

        if isinstance(profile, str):
            params["mode"] = profile
        elif isinstance(profile, self.RoutingMode):
            params["mode"] = profile.make_routing_mode()

        if intervals is not None:
            params["range"] = convert._delimit_list(intervals, ',')

        if interval_type is not None:
            params["rangeType"] = interval_type

        if single_component is not None:
            params["singleComponent"] = convert._convert_bool(single_component)

        if max_points is not None:
            params["maxPoints"] = max_points

        if quality is not None:
            params["quality"] = quality

        if json_attributes is not None:
            params["jsonAttributes"] = json_attributes

        if json_callback is not None:
            params["jsonCallback"] = json_callback

        if truck_type is not None:
            params["truckType"] = truck_type

        if trailers_count is not None:
            params["trailersCount"] = trailers_count

        if shipped_hazardous_goods is not None:
            params["shippedHazardousGoods"] = convert._delimit_list(
                shipped_hazardous_goods, ',')

        if limited_weight is not None:
            params["limitedWeight"] = limited_weight

        if weight_per_axle is not None:
            params["weightPerAxle"] = weight_per_axle

        if height is not None:
            params["height"] = height

        if width is not None:
            params["width"] = width

        if length is not None:
            params["length"] = length

        if tunnel_category is not None:
            params["tunnelCategory"] = convert._delimit_list(
                tunnel_category, ',')

        if consumption_model is not None:
            params["consumptionModel"] = consumption_model

        if custom_consumption_details is not None:
            params["customConsumptionDetails"] = custom_consumption_details

        if speed_profile is not None:
            params["speedProfile"] = speed_profile

        return self._parse_isochrone_json(
            self._request(
                convert._delimit_list(["/calculateisoline", format], '.'),
                get_params=params,
                dry_run=dry_run), intervals)

    @staticmethod
    def _parse_isochrone_json(response, intervals):
        if response is None:
            return None

        geometries = []
        for idx, isochrones in enumerate(response['response']['isoline']):
            range_polygons = []
            if 'component' in isochrones:
                for component in isochrones['component']:
                    if 'shape' in component:
                        coordinates_list = []
                        for coordinates in component['shape']:
                            coordinates_list.append(
                                [float(f) for f in coordinates.split(",")])
                        range_polygons.append(coordinates_list)

            geometries.append(
                Isochrone(
                    geometry=range_polygons,
                    range=intervals[idx],
                    center=list(response['response']['start']
                                ['mappedPosition'].values())))

        return Isochrones(isochrones=geometries, raw=response)

    def distance_matrix(
            self,
            coordinates,
            profile,
            format='json',
            sources=None,
            destinations=None,
            search_range=None,
            avoid_areas=None,
            avoid_links=None,
            avoid_turns=None,
            exclude_countries=None,
            departure=None,
            matrix_attributes=None,
            summary_attributes=['traveltime', 'costfactor', 'distance'],
            truck_type=None,
            trailers_count=None,
            shipped_hazardous_goods=None,
            limited_weight=None,
            weight_per_axle=None,
            height=None,
            width=None,
            length=None,
            tunnel_category=None,
            speed_profile=None,
            dry_run=None):
        """ Gets travel distance and time for a matrix of origins and destinations.

            :param coordinates: The coordinates tuple the route should be calculated
                from in order of visit. Can be a list/tuple of [lon, lat] or :class:`HereMaps.WayPoint` instance or a
                combination of those. For further explanation, see
                https://developer.here.com/documentation/routing/topics/resource-param-type-waypoint.html
            :type coordinates: list of list or list of :class:`HereMaps.WayPoint`

            :param profile: Specifies the routing mode of transport and further options.
                Can be a str or :class:`HereMaps.RoutingMode`
                https://developer.here.com/documentation/routing/topics/resource-param-type-routing-mode.html
            :type profile: str or :class:`HereMaps.RoutingMode`

            :param sources: The starting points for the matrix. 
                Specifies an index referring to coordinates.
            :type sources: list of int

            :param destinations: The destination points for the routes. 
                Specifies an index referring to coordinates.
            :type destinations: list of int

            :param search_range: Defines the maximum search range for destination 
                waypoints, in meters. This parameter is especially useful for optimizing 
                matrix calculation where the maximum desired effective distance is known 
                in advance. Destination waypoints with a longer effective distance than 
                specified by searchRange will be skipped. The parameter is optional. 
                In pedestrian mode the default search range is 20 km. 
                If parameter is omitted in other modes, no range limit will apply.
            :type search_range: int

            :param avoid_areas: Areas which the route must not cross. 
                Array of BoundingBox. Example with 2 bounding boxes
                https://developer.here.com/documentation/routing/topics/resource-param-type-bounding-box.html
            :type avoid_areas: list of list of list

            :param avoid_links: Links which the route must not cross. 
              The list of LinkIdTypes.
            :type avoid_areas: list of string

            :param avoid_turns: List of turn types that the route should avoid. Defaults to empty list. 
              https://developer.here.com/documentation/routing/topics/resource-type-enumerations.html
            :type avoid_turns: str  

            :param exclude_countries: Countries that must be excluded from route calculation. 
            :type exclude_countries: list of str

            :param departure: Time when travel is expected to start. Traffic speed and 
                incidents are taken into account
                when calculating the route (note that in case of a past
                departure time the historical traffic is limited to one year).  
                You can use now to specify the current time. Specify either departure 
                or arrival, not both. When the optional timezone offset is not 
                specified, the time is assumed to be the local.
                Formatted as iso time, e.g. 2018-07-04T17:00:00+02.
            :type departure: str

            :param matrix_attributes: Defines which attributes are included in the 
              response as part of the data representation of the route matrix entries. 
              Defaults to indices and summary. 
              https://developer.here.com/documentation/routing/topics/resource-calculate-matrix.html#resource-calculate-matrix__matrix-route-attribute-type
            :type matrix_attributes: list of str

            :param summary_attributes: Defines which attributes are included in 
                the response as part of the data representation of the matrix 
                entries summaries. Defaults to costfactor.  
                https://developer.here.com/documentation/routing/topics/resource-calculate-matrix.html#resource-calculate-matrix__matrix-route-summary-attribute-type
            :type matrix_attributes: list of str

            :param truck_type: Truck routing only, specifies the vehicle type. 
                Defaults to truck.
            :type truck_type: str

            :param trailers_count: Truck routing only, specifies number of 
                trailers pulled by a vehicle. The provided value must be between 0 and 4. 
                Defaults to 0.
            :type trailers_count: int

            :param shipped_hazardous_goods: Truck routing only, list of hazardous
                materials in the vehicle. Please refer to the enumeration type 
                HazardousGoodTypeType for available values. Note the value 
                allhazardousGoods does not apply to the request parameter.
                https://developer.here.com/documentation/routing/topics/resource-type-enumerations.html#resource-type-enumerations__enum-hazardous-good-type-type
            :type shipped_hazardous_goods: list of str

            :param limited_weight: Truck routing only, vehicle weight including 
                trailers and shipped goods, in tons. The provided value must be 
                between 0 and 1000.
            :type limited_weight: int

            :param weight_per_axle: Truck routing only, vehicle weight per axle 
                in tons. The provided value must be between 0 and 1000.
            :type limited_weight: int

            :param height: Truck routing only, vehicle height in meters. The 
                provided value must be between 0 and 50.
            :type height: int

            :param width: Truck routing only, vehicle width in meters. 
                The provided value must be between 0 and 50.
            :type width: int  

            :param length: Truck routing only, vehicle length in meters. 
                The provided value must be between 0 and 300.
            :type length: int        

            :param tunnel_category: Truck routing only, specifies the tunnel 
                category to restrict certain route links. The route will pass 
                only through tunnels of a less strict category.
            :type tunnel_category: list of str

            :param speed_profile: Specifies the speed profile variant for a given 
                routing mode. The speed profile affects travel time estimation as 
                well as roads evaluation when computing the fastest route. 
                Note that computed routes might differ depending on a used profile.
                https://developer.here.com/documentation/routing/topics/resource-param-type-speed-profile-type.html
            :type speed_profile: str

            :param dry_run: Print URL and parameters without sending the request.
            :param dry_run: bool

            :returns: raw JSON response
            :rtype: dict
            """
        self.base_url = 'https://matrix.route.api.here.com/routing/7.2'
        params = {}

        params["app_code"] = self.app_code
        params["app_id"] = self.app_id

        try:
            for i, start_idx in enumerate(sources):

                if isinstance(coordinates[start_idx], self.WayPoint):
                    params["start" +
                           str(i)] = coordinates[start_idx].make_waypoint()
                elif isinstance(coordinates[start_idx], (list, tuple)):
                    params["start" + str(i)] = 'geo!' + convert._delimit_list([
                        convert._format_float(f)
                        for f in coordinates[start_idx]
                    ], ',')

        except IndexError:
            raise IndexError(
                "Parameter sources out of coordinates range at index {}.".
                format(start_idx))
        except TypeError:
            raise TypeError("Please add sources indices.")

        try:
            for i, dest_idx in enumerate(destinations):

                if isinstance(coordinates[dest_idx], self.WayPoint):
                    params["destination" +
                           str(i)] = coordinates[dest_idx].make_waypoint()
                elif isinstance(coordinates[dest_idx], (list, tuple)):
                    params["destination" +
                           str(i)] = 'geo!' + convert._delimit_list([
                               convert._format_float(f)
                               for f in coordinates[dest_idx]
                           ], ',')

        except IndexError:
            raise IndexError(
                "Parameter destinations out of coordinates range at index {}.".
                format(dest_idx))
        except TypeError:
            raise TypeError("Please add destinations indices.")

        if isinstance(profile, str):
            params["mode"] = profile
        elif isinstance(profile, self.RoutingMode):
            params["mode"] = profile.make_routing_mode()

        if search_range is not None:
            params["searchRange"] = search_range

        if avoid_areas is not None:
            params["avoidAreas"] = convert._delimit_list([
                convert._delimit_list([
                    convert._delimit_list(
                        [convert._format_float(f) for f in pair], ',')
                    for pair in bounding_box
                ], ';') for bounding_box in avoid_areas
            ], '!')

        if avoid_links is not None:
            params["avoidLinks"] = convert._delimit_list(avoid_links, ',')

        if avoid_turns is not None:
            params["avoidTurns"] = avoid_turns

        if exclude_countries is not None:
            params["excludeCountries"] = convert._delimit_list(
                exclude_countries, ',')

        if departure is not None:
            params["departure"] = departure.isoformat()

        if matrix_attributes is not None:
            params["matrixAttributes"] = convert._delimit_list(
                matrix_attributes, ',')

        if summary_attributes is not None:
            params["summaryAttributes"] = convert._delimit_list(
                summary_attributes, ',')

        if truck_type is not None:
            params["truckType"] = truck_type

        if trailers_count is not None:
            params["trailersCount"] = trailers_count

        if shipped_hazardous_goods is not None:
            params["shippedHazardousGoods"] = convert._delimit_list(
                shipped_hazardous_goods, ',')

        if limited_weight is not None:
            params["limitedWeight"] = limited_weight

        if weight_per_axle is not None:
            params["weightPerAxle"] = weight_per_axle

        if height is not None:
            params["height"] = height

        if width is not None:
            params["width"] = width

        if length is not None:
            params["length"] = length

        if tunnel_category is not None:
            params["tunnelCategory"] = convert._delimit_list(
                tunnel_category, ',')

        if speed_profile is not None:
            params["speedProfile"] = speed_profile

        return self._parse_matrix_json(
            self._request(
                convert._delimit_list(["/calculatematrix", format], '.'),
                get_params=params,
                dry_run=dry_run))

    @staticmethod
    def _parse_matrix_json(response):
        if response is None:
            return None

        durations = []
        distances = []
        index_durations = []
        index_distances = []

        next_ = None
        mtx_objects = response['response']['matrixEntry']
        l = len(mtx_objects)
        for index, obj in enumerate(mtx_objects):
            if index < (l - 1):
                next_ = mtx_objects[index + 1]

            if 'travelTime' in obj['summary']:
                index_durations.append(obj['summary']['travelTime'])
            else:
                index_durations.append(obj['summary']['costfactor'])

            if 'distance' in obj['summary']:
                index_distances.append(obj['summary']['distance'])

            if next_['startIndex'] > obj['startIndex']:
                durations.append(index_durations)
                distances.append(index_distances)
                index_durations = []
                index_distances = []

        durations.append(index_durations)
        distances.append(index_distances)

        return Matrix(durations=durations, distances=distances, raw=response)