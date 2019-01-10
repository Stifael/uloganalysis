from abc import ABCMeta, abstractmethod
import os
from uloganalysis import loginfo
from uloganalysis import ulogconv as conv


class dfUlgBase(metaclass=ABCMeta):
    """
    Base class for converting .ulg file into ulog-structure and pandas-dataframe
    """

    def __init__(self, df, ulog, topics):
        """
        Args:
            df (pandas): dataframe of uORB msgs from topics
            ulog (pyulog-struct): struct of uORB msgs (without resampling)
            topics (list): topics that are used to generate df and ulog
        """
        self.df = df  # pandas dataframe
        self.ulog = ulog  # ulog
        self.topics = topics  # PX4-uorb topics

    @classmethod
    def _check_file(self, filepath):
        """
        Method to check if file is an .ulg file

        Args:
            filepath: path to .ulg-file
        """
        if os.path.isfile(filepath):
            base, ext = os.path.splitext(filepath)
            if ext.lower() not in (".ulg"):
                raise Exception("File is not .ulg file")
        else:
            raise Exception("File does not exist")

    @classmethod
    def create(cls, filepath, topics=None, zoh_topics=None):
        """
        Factory method to create a dfulgBase object

        By default, the merge-method uses linear interpolation for resampling.
        Dataframe (df) is a pandas-dataframe with index equal to the merged timestamps. Each column represents a message-field.
        For instance, the thrust-field of the message vehicle_local_position_setpoint message would be named as follow:
            T_vehicle_local_position_setpoint_0__F_thrust_x
        if the field x of vehicle_local_position_setpoint is a scalar or
            T_vehicle_local_position_setpoint_0__F_x_0
        if the field x is an array, where the 0 represents the index of the array.
        The T stands for topic, which indicates the beginning of the topic. In this example, the topcic name is vehicle_local_position_setpoint.
        The topic name is followed by a number, which indicates the topic instance. If there is only one instance of a specific topic, then this number will be 0.
        The instance number is followed by two underlines and a capital letter F, which stands for field. In the example above, the field in question is x.

        Args:
            filepath: path to .ulg file
            topics: topics from which pandas-dataframe and ulog-struct are constructed from
            zoh_topics: topics which are resampled through zoh
        """

        # check if valid file is provided
        cls._check_file(filepath)

        # Add required topics to topics if not already present
        if topics is not None:
            topics = topics.extend(
                x for x in cls.get_required_topics() if x not in topics
            )
        else:
            topics = cls.get_required_topics()

        ulog = loginfo.get_ulog(filepath, topics)

        # Add required zoh-topics if not already present
        if zoh_topics is not None:
            zoh = zoh_topics.extend(
                x for x in cls.get_required_zoh_topics() if x not in zoh_topics
            )
        else:
            zoh = cls.get_required_zoh_topics()

        if ulog is None:
            raise Exception("Ulog is empty")

        pandadict = conv.createPandaDict(ulog)
        df = conv.merge(pandadict, zoh)
        # change to seconds
        df.timestamp = (df.timestamp - df.timestamp[0]) * 1e-6
        return cls(df, ulog, topics)

    @classmethod
    @abstractmethod
    def get_required_topics(self):
        """
        Abstract method to get required topic
        """
        pass

    @classmethod
    @abstractmethod
    def get_required_zoh_topics(self):
        """
        Abstract method to get the topics on which zoh-resampling were applied.
        """
        pass
