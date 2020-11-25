from pprint import pprint
from typing import Tuple, Optional

import inquirer

from poc.questions import Text, Confirm, Section, Config


def get_kubernetes_work_nodes():
    return 3


class KafkaReplicasQ(Text):
    name = "kafka_replicas"
    message = f"Enter number of kafka replicas to use between (1,{get_kubernetes_work_nodes()})"
    default = "3"

    def validate(self, value) -> bool:
        if not value.isdigit:
            return False

        int_value = int(value)
        if not 0 <= int_value <= get_kubernetes_work_nodes():
            return False

        return True


class KafkaExternalAccessQ(Confirm):
    name = "kafka-external-access"
    message = "Expose kafka outside"
    default = False


class KafkaExternalAccessAutoDiscoveryQ(Confirm):
    name = "kafka-external-access-autodiscover"
    message = "Autodiscover Load Balancer IPs that expose kafka pods"

    def __init__(self, dependencies: Tuple[KafkaExternalAccessQ]):
        super().__init__(dependencies)

    @property
    def default(self) -> Optional[bool]:
        kafka_external_access = self.resolve_dependency(self.dependencies[0])
        if not kafka_external_access:
            return False

        return None

    @property
    def ignore(self) -> bool:
        kafka_external_access = self.resolve_dependency(self.dependencies[0])
        if not kafka_external_access:
            return True

        return super().ignore


class KafkaExternalAccessLoadBalancerIpsQ(Text):
    name = "kafka-external-access-load-balancer-ips"
    message = "Comma separated Load Balancer IPs that expose kafka(e.g. <ip_1>,<ip_2>)"
    default = ""
    show_default = False

    @property
    def ignore(self) -> bool:
        kafka_external_access = self.resolve_dependency(self.dependencies[0])
        kafka_external_access_auto_discovery = self.resolve_dependency(self.dependencies[1])

        if not kafka_external_access or kafka_external_access_auto_discovery:
            return True

        return False

    def __init__(self, dependencies: Tuple[KafkaExternalAccessQ, KafkaExternalAccessAutoDiscoveryQ]):
        super().__init__(dependencies)


kafka_replicas_q = KafkaReplicasQ()

kafka_external_access_q = KafkaExternalAccessQ()

kafka_external_access_auto_discovery_q = KafkaExternalAccessAutoDiscoveryQ(
    dependencies=(kafka_external_access_q,)
)

kafka_external_access_load_balancer_ips_q = KafkaExternalAccessLoadBalancerIpsQ(
    dependencies=(kafka_external_access_q, kafka_external_access_auto_discovery_q)
)


if __name__ == "__main__":
    questions = (
        kafka_replicas_q,
        kafka_external_access_q,
        kafka_external_access_auto_discovery_q,
        kafka_external_access_load_balancer_ips_q
    )

    kafka_section = Section(
        name="kafka",
        questions=questions,
        answers={'version': '0.1'}  # empty dict breaks answers sharing mechanism
    )

    config = Config(
        sections=(kafka_section,)
    )

    for section in config.sections:
        inquirer.prompt(questions, answers=section.answers)

    pprint(config.answers)
