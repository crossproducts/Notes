# Kafka

## Notes
- **Topic**:
  - A topic in Kafka is split into partitions
- **Partitions**:
  - 1 partition → 1 consumer max
  - 10 partitions → 10 consumers max
- **Offset**: 
  - Message position in a partition
  - Offsets are sequential numbers
  - Offsets are unique only within a partition
  - Kafka does not reuse offsets
- **Message Ordering**: 
  - Kafka guarantees ordering only within a partition.
- **Partition Key**: 
  - Kafka uses the key to decide which partition to send to
  - When a producer sends data, it may include a key
- Exactly Once Processing
  - Apache Spark
  - Apacke Flink
- Producers
- Consumers
- Brokers
- Zookeeper
- KRaft


## References
- [Udemy - Apache Kafka Series - Learn Apache Kafka for Beginners v3](https://www.udemy.com/course/apache-kafka/?srsltid=AfmBOooHgJ2zPYPQgZN-J2sdG0vYirGkenl3hp73IewepV-UJsrg-J1f)