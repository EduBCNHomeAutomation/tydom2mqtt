import json
import logging
from .Sensor import Sensor

logger = logging.getLogger(__name__)
awning_command_topic = "awning/tydom/{id}/set_positionCmd"
awning_config_topic = "homeassistant/cover/tydom/{id}/config"
awning_position_topic = "awning/tydom/{id}/current_position"
awning_set_position_topic = "awning/tydom/{id}/set_position"
awning_attributes_topic = "awning/tydom/{id}/attributes"


class Awning:
    def __init__(self, tydom_attributes, set_position=None, mqtt=None):
        self.device = None
        self.config = None
        self.config_topic = None
        self.attributes = tydom_attributes
        self.device_id = self.attributes['device_id']
        self.endpoint_id = self.attributes['endpoint_id']
        self.id = self.attributes['id']
        self.name = self.attributes['awning_name']
        self.set_position = set_position

        logger.debug ('Evaluating TYDOM attributes %s',tydom_attributes)
        if 'position' in tydom_attributes:
            logger.debug ('Position in awning attributes')
            self.current_position = self.attributes['position']

        self.mqtt = mqtt

    async def setup(self):  
        self.device = {
            'manufacturer': 'Delta Dore',
            'model': 'Volet',
            'name': self.name,
            'identifiers': self.id}
        self.config_topic = awning_config_topic.format(id=self.id)
        self.config = {
            'name': self.name,
            'unique_id': self.id,
            'command_topic': awning_command_topic.format(
                id=self.id),
            'set_position_topic': awning_set_position_topic.format(
                id=self.id),
            'position_topic': awning_position_topic.format(
                id=self.id),
            'payload_open': "UP",
            'payload_close': "DOWN",
            'payload_stop': "STOP",
            'retain': 'false',
            'device': self.device,
            'device_class': 'shutter'}

        self.config['json_attributes_topic'] = awning_attributes_topic.format(
            id=self.id)

        if self.mqtt is not None:
            self.mqtt.mqtt_client.publish(
                self.config_topic, json.dumps(
                    self.config), qos=0, retain=True)

    async def update(self):
        await self.setup()

        try:
            await self.update_sensors()
        except Exception as e:
            logger.error("Awning sensors Error :")
            logger.error(e)

        if self.mqtt is not None and 'position' in self.attributes:
            self.mqtt.mqtt_client.publish(
                self.config['position_topic'],
                self.current_position,
                qos=0, retain=True)

        if self.mqtt is not None:
            self.mqtt.mqtt_client.publish(
                self.config['json_attributes_topic'], self.attributes, qos=0, retain=True)

        logger.info(
            "Awning created / updated : %s %s",
            self.name,
            self.id)

    async def update_sensors(self):
        for i, j in self.attributes.items():
            if not i == 'device_type' or not i == 'id':
                new_sensor = Sensor(
                    elem_name=i,
                    tydom_attributes_payload=self.attributes,
                    mqtt=self.mqtt)
                await new_sensor.update()

    async def put_position(tydom_client, device_id, awning_id, position):
        logger.info("%s %s %s", awning_id, 'position', position)
        if not (position == ''):
            await tydom_client.put_devices_data(device_id, awning_id, 'position', position)

    async def put_positionCmd(tydom_client, device_id, awning_id, positionCmd):
        logger.info("%s %s %s", awning_id, 'positionCmd', positionCmd)
        if not (positionCmd == ''):
            await tydom_client.put_devices_data(device_id, awning_id, 'positionCmd', positionCmd)
