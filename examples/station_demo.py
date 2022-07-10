from abc import ABC

from pydsol.core.experiment import Replication, SingleReplication
from pydsol.core.interfaces import ReplicationInterface
from pydsol.core.model import DSOLModel
from pydsol.core.pubsub import EventProducer, EventType, EventListener, Event
from pydsol.core.simulator import DEVSSimulator, DEVSSimulatorFloat
from pydsol.core.statistics import SimCounter, SimTally, SimPersistent


class Entity():
    __glob_nr = 0
    
    @classmethod
    def uniq_nr(cls) -> int:
        cls.__glob_nr += 1
        return cls.__glob_nr

    def __init__(self, create_time: float):
        self.nr = self.uniq_nr()
        self.create_time = create_time
        print(f"Entity {self} created at t={create_time}")

    def __str__(self):
        return f"E{self.nr:02}"
    
    def __repr__(self):
        return str(self)


class Station(EventProducer, ABC):

    def __init__(self, simulator: DEVSSimulator):
        EventProducer.__init__(self)
        self.simulator = simulator
        self.next: Station = None
        

class Generator(Station):

    GENERATED_EVENT: EventType = EventType("GENERATED_EVENT")

    def __init__(self, simulator: DEVSSimulator, iat: float):
        super().__init__(simulator)
        self.iat = iat
        self.simulator.schedule_event_rel(self.iat, self, "generate")

    def generate(self):
        t: float = self.simulator.simulator_time
        entity: Entity = Entity(t)
        self.next.arrive(entity)
        self.fire_timed(t, Generator.GENERATED_EVENT, 1) 
        self.simulator.schedule_event_rel(self.iat, self, "generate")

        
class Server(Station):

    BUSY_EVENT: EventType = EventType("BUSY_EVENT")
    IN_QUEUE_TIME_EVENT: EventType = EventType("IN_QUEUE_TIME_EVENT")
    QUEUE_LEN_EVENT: EventType = EventType("QUEUE_LEN_EVENT")
    PROCESS_TIME_EVENT: EventType = EventType("PROCESS_TIME_EVENT")
    
    def __init__(self, simulator: DEVSSimulator, pt: float):
        super().__init__(simulator)
        self.pt = pt
        self.queue = []  # contains (in_time, entity) tuples
        self.fire_queue()
        self.process_entity = None
        self.process_entity_time = None
        self.set_busy(0)

    def arrive(self, entity: Entity):
        t: float = self.simulator.simulator_time
        if self.process_entity == None:
            self.process_entity = entity
            self.start_process_time = t
            self.set_busy(1)
            self.simulator.schedule_event_rel(self.pt, self, "depart")
            print(f"Entity {entity} processing started at {t}"\
                  +f", queue={self.queue}")
        else:
            self.queue.append((t, entity))
            self.fire_queue()
            print(f"Entity {entity} in queue at {t}"\
                  +f", queue={self.queue}")
            
    def depart(self):
        t: float = self.simulator.simulator_time
        ready_entity: Entity = self.process_entity
        busytime: float = t - self.start_process_time
        self.fire_timed(t, Server.PROCESS_TIME_EVENT, busytime)
        print(f"Entity {ready_entity} ready processing at {t}"\
                  +f", busytime={busytime}, queue={self.queue}")
        self.next.arrive(ready_entity)
        if len(self.queue) == 0:
            print("Server: busy = 0, queue is empty")
            self.set_busy(0)
            self.process_entity = None
            self.process_entity_time = None
        else:
            entry = self.queue.pop(0)
            self.fire_queue()
            inqueuetime: float = t - entry[0]
            self.fire_timed(t, Server.IN_QUEUE_TIME_EVENT, inqueuetime)
            entity: Entity = entry[1]
            print(f"Entity {entity} left the queue at {t}"\
                              +f", queue={self.queue}, queue time={inqueuetime}")
            self.process_entity = entity
            self.start_process_time = t
            self.set_busy(1)
            self.simulator.schedule_event_rel(self.pt, self, "depart")
            print(f"Entity {entity} processing started at {t}"\
                              +f", queue={self.queue}")

    def fire_queue(self):
        t: float = self.simulator.simulator_time
        self.fire_timed(t, Server.QUEUE_LEN_EVENT, len(self.queue))
        
    def set_busy(self, busy):
        self.busy = busy
        self.fire_timed(self.simulator.simulator_time,
                        Server.BUSY_EVENT, busy) 


class Sink(Station):

    SYS_TIME_EVENT: EventType = EventType("SYS_TIME_EVENT")
    
    def __init__(self, simulator: DEVSSimulator):
        super().__init__(simulator)

    def arrive(self, entity: Entity):
        t: float = self.simulator.simulator_time
        time_in_system: float = t - entity.create_time
        self.fire_timed(t, Sink.SYS_TIME_EVENT, time_in_system)
        print(f"Entity {entity} leaves at t={t}, systime={time_in_system}")


class QueuingModel(DSOLModel):
    
    def __init__(self, simulator: DEVSSimulator):
        super().__init__(simulator)
    
    def construct_model(self):
        generator: Generator = Generator(self.simulator, 1.5)
        server: Server = Server(self.simulator, 2.0)
        sink: Sink = Sink(self.simulator)
        generator.next = server
        server.next = sink
        
        self.gen_counter: SimCounter = SimCounter("generator.nr",
            "number of generated entities", self.simulator)
        self.gen_counter.listen_to(generator, Generator.GENERATED_EVENT)
        self.tiq_tally: SimTally = SimTally("server.time_in_queue", 
            "server time in queue of entities", self.simulator)
        self.tiq_tally.listen_to(server, Server.IN_QUEUE_TIME_EVENT)
        self.spt_tally: SimTally = SimTally("server.proc_time", 
            "server processing time of entities", self.simulator)
        self.spt_tally.listen_to(server, Server.PROCESS_TIME_EVENT)
        self.tis_tally: SimTally = SimTally("entity.time_in_sys", 
            "entity time in system", self.simulator)
        self.tis_tally.listen_to(sink, Sink.SYS_TIME_EVENT)
        self.sql_persistent: SimPersistent = SimPersistent("server.queue_len", 
            "server queue length", self.simulator)
        self.sql_persistent.listen_to(server, Server.QUEUE_LEN_EVENT)
        self.sut_persistent: SimPersistent = SimPersistent("server.util", 
            "server time-weighted utilization", self.simulator)
        self.sut_persistent.listen_to(server, Server.BUSY_EVENT)


class Simulation(EventListener):

    def __init__(self):
        self.simulator: DEVSSimulatorFloat = DEVSSimulatorFloat("sim")
        self.simulator.add_listener(ReplicationInterface.END_REPLICATION_EVENT, self)
        self.model: QueuingModel = QueuingModel(self.simulator)
        self.replication: Replication = SingleReplication("rep", 0.0, 0.0, 100.0)
        self.simulator.initialize(self.model, self.replication)
        self.simulator.start()

    def notify(self, event: Event):
        if event.event_type == ReplicationInterface.END_REPLICATION_EVENT:
            self.report()
    
    def report(self):
        print("\n\nEnd simulation\n")
        print(self.model.gen_counter.report_header())
        print(self.model.gen_counter.report_line())
        print(self.model.gen_counter.report_footer())
        print()
        print(self.model.tiq_tally.report_header())
        print(self.model.tiq_tally.report_line())
        print(self.model.spt_tally.report_line())
        print(self.model.tis_tally.report_line())
        print(self.model.tiq_tally.report_footer())
        print()
        print(self.model.sql_persistent.report_header())
        print(self.model.sql_persistent.report_line())
        print(self.model.sut_persistent.report_line())
        print(self.model.sql_persistent.report_footer())

if __name__ == "__main__":
    Simulation()
