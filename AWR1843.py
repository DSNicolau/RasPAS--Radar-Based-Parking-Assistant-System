import serial
import time
import numpy as np
import platform

byteBuffer = np.zeros(2**15, dtype="uint8")
byteBufferLength = 0


def serialConfig(configFileName):
    """
    Configure the serial ports and send data from a configuration file to the radar.

    Parameters:
        configFileName (str): The path to the configuration file.

    Returns:
        tuple: A tuple containing:
            - CLIport (Serial): The serial port for configuration.
            - Dataport (Serial): The serial port for data transmission.

    """

    # Define global variables to store serial ports
    global CLIport
    global Dataport

    # Detect the operating system and configure serial ports accordingly
    if platform.system() == "Linux":
        CLIport = serial.Serial("/dev/ttyACM0", 115200)
        Dataport = serial.Serial("/dev/ttyACM1", 921600)

    elif platform.system() == "Windows":
        CLIport = serial.Serial("COM4", 115200)
        Dataport = serial.Serial("COM3", 921600)

    # Read configuration data from the file and send it to the radar
    config = [line.rstrip("\r\n") for line in open(configFileName)]

    for i in config:
        # Write each line from the configuration file to the CLI port
        CLIport.write((i + "\n").encode())
        # Add a short delay to allow time for the radar to process the command
        time.sleep(0.01)

    # Return the configured serial ports
    return CLIport, Dataport


def parseConfigFile(configFileName, numRxAnt=1, numTxAnt=1):
    """
    Parse the configuration file for radar parameters.

    Parameters:
        configFileName (str): The path to the configuration file.
        numRxAnt (int): Number of receiving antennas (default is 1).
        numTxAnt (int): Number of transmitting antennas (default is 1).

    Returns:
        dict: A dictionary containing radar configuration parameters.

    """

    # Initialize an empty dictionary to store radar configuration parameters
    configParameters = {}

    # Read the configuration file and process each line
    config = [line.rstrip("\r\n") for line in open(configFileName)]
    for i in config:
        # Split each line by space to extract information
        splitWords = i.split(" ")

        # Check if the line contains profile configuration information
        if "profileCfg" in splitWords[0]:
            # Extract profile configuration parameters
            startFreq = int(float(splitWords[2]))
            idleTime = int(splitWords[3])
            rampEndTime = float(splitWords[5])
            freqSlopeConst = float(splitWords[8])
            numAdcSamples = int(splitWords[10])
            numAdcSamplesRoundTo2 = 1

            # Adjust the number of ADC samples to the nearest power of 2
            while numAdcSamples > numAdcSamplesRoundTo2:
                numAdcSamplesRoundTo2 = numAdcSamplesRoundTo2 * 2

            digOutSampleRate = int(splitWords[11])

        # Check if the line contains frame configuration information
        elif "frameCfg" in splitWords[0]:
            # Extract frame configuration parameters
            chirpStartIdx = int(splitWords[1])
            chirpEndIdx = int(splitWords[2])
            numLoops = int(splitWords[3])
            numFrames = int(splitWords[4])
            framePeriodicity = float(splitWords[5])

    # Calculate additional radar parameters using the extracted configuration
    numChirpsPerFrame = (chirpEndIdx - chirpStartIdx + 1) * numLoops
    configParameters["numDopplerBins"] = numChirpsPerFrame // numTxAnt
    configParameters["numRangeBins"] = numAdcSamplesRoundTo2
    configParameters["rangeResolutionMeters"] = (3e8 * digOutSampleRate * 1e3) / (
        2 * freqSlopeConst * 1e12 * numAdcSamples
    )
    configParameters["rangeIdxToMeters"] = (3e8 * digOutSampleRate * 1e3) / (
        2 * freqSlopeConst * 1e12 * configParameters["numRangeBins"]
    )
    configParameters["dopplerResolutionMps"] = 3e8 / (
        2
        * startFreq
        * 1e9
        * (idleTime + rampEndTime)
        * 1e-6
        * configParameters["numDopplerBins"]
        * numTxAnt
    )
    configParameters["maxRange"] = (300 * 0.9 * digOutSampleRate) / (
        2 * freqSlopeConst * 1e3
    )
    configParameters["maxVelocity"] = 3e8 / (
        4 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * numTxAnt
    )

    # Return the dictionary containing radar configuration parameters
    return configParameters


def readAndParseData18xx_3d(Dataport, configParameters):
    """
    Read and parse incoming data in 3D format.

    Parameters:
        Dataport (Serial): The serial port for data reception.
        configParameters (dict): Radar configuration parameters.

    Returns:
        tuple: A tuple containing:
            - dataOK (bool): Indicates if data was read correctly.
            - frameNumber (int): The frame number.
            - detObj (dict): A dictionary containing detected object information.

    """
    global byteBuffer, byteBufferLength

    # Define constants
    MMWDEMO_UART_MSG_DETECTED_POINTS = 1
    MMWDEMO_OUTPUT_MSG_RANGE_DOPPLER_HEAT_MAP = 5
    maxBufferSize = 2**15
    magicWord = [2, 1, 4, 3, 6, 5, 8, 7]

    # Initialize variables
    magicOK = 0  # Checks if magic number has been read
    dataOK = 0  # Checks if the data has been read correctly
    frameNumber = 0
    detObj = {}

    # Read data from the serial port
    readBuffer = Dataport.read(Dataport.in_waiting)
    byteVec = np.frombuffer(readBuffer, dtype="uint8")
    byteCount = len(byteVec)

    # Add received data to the buffer
    if (byteBufferLength + byteCount) < maxBufferSize:
        byteBuffer[byteBufferLength : byteBufferLength + byteCount] = byteVec[
            :byteCount
        ]
        byteBufferLength = byteBufferLength + byteCount

    # Check if buffer contains enough data
    if byteBufferLength > 16:
        # Check for all possible locations of the magic word
        possibleLocs = np.where(byteBuffer == magicWord[0])[0]

        # Confirm the presence of the magic word and store the index in startIdx
        startIdx = []
        for loc in possibleLocs:
            check = byteBuffer[loc : loc + 8]
            if np.all(check == magicWord):
                startIdx.append(loc)

        # Check if startIdx is not empty
        if startIdx:
            # Remove data before the first start index
            if startIdx[0] > 0 and startIdx[0] < byteBufferLength:
                byteBuffer[: byteBufferLength - startIdx[0]] = byteBuffer[
                    startIdx[0] : byteBufferLength
                ]
                byteBuffer[byteBufferLength - startIdx[0] :] = np.zeros(
                    len(byteBuffer[byteBufferLength - startIdx[0] :]), dtype="uint8"
                )
                byteBufferLength = byteBufferLength - startIdx[0]

            # Ensure no errors with the byte buffer length
            if byteBufferLength < 0:
                byteBufferLength = 0

            # Word array to convert 4 bytes to a 32-bit number
            word = [1, 2**8, 2**16, 2**24]

            # Read the total packet length
            totalPacketLen = np.matmul(byteBuffer[12 : 12 + 4], word)

            # Check if entire packet has been read
            if (byteBufferLength >= totalPacketLen) and (byteBufferLength != 0):
                magicOK = 1

    # If magicOK is 1, process the message
    if magicOK:
        # Word array to convert 4 bytes to a 32-bit number
        word = [1, 2**8, 2**16, 2**24]

        # Initialize pointer index
        idX = 28

        # Read the header
        magicNumber = byteBuffer[idX : idX + 8]
        idX += 8
        version = format(np.matmul(byteBuffer[idX : idX + 4], word), "x")
        idX += 4
        totalPacketLen = np.matmul(byteBuffer[idX : idX + 4], word)
        idX += 4
        platform = format(np.matmul(byteBuffer[idX : idX + 4], word), "x")
        idX += 4
        frameNumber = np.matmul(byteBuffer[idX : idX + 4], word)
        idX += 4
        timeCpuCycles = np.matmul(byteBuffer[idX : idX + 4], word)
        idX += 4
        numDetectedObj = np.matmul(byteBuffer[idX : idX + 4], word)
        idX += 4
        numTLVs = np.matmul(byteBuffer[idX : idX + 4], word)
        idX += 4
        subFrameNumber = np.matmul(byteBuffer[idX : idX + 4], word)
        idX += 4

        # Read the TLV messages
        for tlvIdx in range(numTLVs):
            # Word array to convert 4 bytes to a 32-bit number
            word = [1, 2**8, 2**16, 2**24]

            # Check the TLV message header
            tlv_type = np.matmul(byteBuffer[idX : idX + 4], word)
            idX += 4
            tlv_length = np.matmul(byteBuffer[idX : idX + 4], word)
            idX += 4

            # Read data based on TLV message type
            if tlv_type == MMWDEMO_UART_MSG_DETECTED_POINTS:
                # Initialize arrays
                x = np.zeros(numDetectedObj, dtype=np.float32)
                y = np.zeros(numDetectedObj, dtype=np.float32)
                z = np.zeros(numDetectedObj, dtype=np.float32)
                velocity = np.zeros(numDetectedObj, dtype=np.float32)

                for objectNum in range(numDetectedObj):
                    # Read data for each object
                    x[objectNum] = byteBuffer[idX : idX + 4].view(dtype=np.float32)
                    idX += 4
                    y[objectNum] = byteBuffer[idX : idX + 4].view(dtype=np.float32)
                    idX += 4
                    z[objectNum] = byteBuffer[idX : idX + 4].view(dtype=np.float32)
                    idX += 4
                    velocity[objectNum] = byteBuffer[idX : idX + 4].view(
                        dtype=np.float32
                    )
                    idX += 4

                # Store data in detObj dictionary
                detObj = {
                    "numObj": numDetectedObj,
                    "x": x,
                    "y": y,
                    "z": z,
                    "velocity": velocity,
                }

                dataOK = 1
            elif tlv_type == MMWDEMO_OUTPUT_MSG_RANGE_DOPPLER_HEAT_MAP:
                # Determine number of bytes to read
                numBytes = (
                    2
                    * configParameters["numRangeBins"]
                    * configParameters["numDopplerBins"]
                )

                # Convert raw data to int16 array
                payload = byteBuffer[idX : idX + numBytes]
                idX += numBytes
                rangeDoppler = payload.view(dtype=np.int16)

                # Some frames have strange values, skip those frames
                if np.max(rangeDoppler) > 10000:
                    continue

                # Convert range doppler array to a matrix
                rangeDoppler = np.reshape(
                    rangeDoppler,
                    (
                        configParameters["numDopplerBins"],
                        configParameters["numRangeBins"],
                    ),
                    "F",
                )
                rangeDoppler = np.append(
                    rangeDoppler[int(len(rangeDoppler) / 2) :],
                    rangeDoppler[: int(len(rangeDoppler) / 2)],
                    axis=0,
                )

                # Generate range and doppler arrays for the plot
                rangeArray = (
                    np.array(range(configParameters["numRangeBins"]))
                    * configParameters["rangeIdxToMeters"]
                )
                dopplerArray = np.multiply(
                    np.arange(
                        -configParameters["numDopplerBins"] / 2,
                        configParameters["numDopplerBins"] / 2,
                    ),
                    configParameters["dopplerResolutionMps"],
                )

        # Remove processed data
        if idX > 0 and byteBufferLength > idX:
            shiftSize = totalPacketLen

            byteBuffer[: byteBufferLength - shiftSize] = byteBuffer[
                shiftSize:byteBufferLength
            ]
            byteBuffer[byteBufferLength - shiftSize :] = np.zeros(
                len(byteBuffer[byteBufferLength - shiftSize :]), dtype="uint8"
            )
            byteBufferLength = byteBufferLength - shiftSize

            # Ensure no errors with buffer length
            if byteBufferLength < 0:
                byteBufferLength = 0

    return dataOK, frameNumber, detObj


def readAndParseData18xx_2d(Dataport, configParameters):
    """
    Read and parse incoming data in 2D format.

    Parameters:
        Dataport (Serial): The serial port for data reception.
        configParameters (dict): Radar configuration parameters.

    Returns:
        tuple: A tuple containing:
            - dataOK (bool): Indicates if data was read correctly.
            - frameNumber (int): The frame number.
            - detObj (dict): A dictionary containing detected object information.

    """
    global byteBuffer, byteBufferLength

    # Constants
    MMWDEMO_UART_MSG_DETECTED_POINTS = 1
    maxBufferSize = 2**15
    magicWord = [2, 1, 4, 3, 6, 5, 8, 7]

    # Initialize variables
    magicOK = 0  # Flag to check if magic number has been read
    dataOK = 0  # Flag to check if the data has been read correctly
    frameNumber = 0
    detObj = {}

    # Read data from the serial port
    readBuffer = Dataport.read(Dataport.in_waiting)
    byteVec = np.frombuffer(readBuffer, dtype="uint8")
    byteCount = len(byteVec)

    # Check if the buffer is not full, then add the data to the buffer
    if (byteBufferLength + byteCount) < maxBufferSize:
        byteBuffer[byteBufferLength : byteBufferLength + byteCount] = byteVec[
            :byteCount
        ]
        byteBufferLength = byteBufferLength + byteCount

    # Check if the buffer has some data
    if byteBufferLength > 16:
        # Check for all possible locations of the magic word
        possibleLocs = np.where(byteBuffer == magicWord[0])[0]

        # Confirm the presence of the magic word and store the index in startIdx
        startIdx = []
        for loc in possibleLocs:
            check = byteBuffer[loc : loc + 8]
            if np.all(check == magicWord):
                startIdx.append(loc)

        # Check if startIdx is not empty
        if startIdx:
            # Remove the data before the first start index
            if startIdx[0] > 0 and startIdx[0] < byteBufferLength:
                byteBuffer[: byteBufferLength - startIdx[0]] = byteBuffer[
                    startIdx[0] : byteBufferLength
                ]
                byteBuffer[byteBufferLength - startIdx[0] :] = np.zeros(
                    len(byteBuffer[byteBufferLength - startIdx[0] :]), dtype="uint8"
                )
                byteBufferLength = byteBufferLength - startIdx[0]

            # Ensure no errors with the byte buffer length
            if byteBufferLength < 0:
                byteBufferLength = 0

            # Word array to convert 4 bytes to a 32-bit number
            word = [1, 2**8, 2**16, 2**24]

            # Read the total packet length
            totalPacketLen = np.matmul(byteBuffer[12 : 12 + 4], word)

            # Check if the entire packet has been read
            if (byteBufferLength >= totalPacketLen) and (byteBufferLength != 0):
                magicOK = 1

    # If magicOK is 1 then process the message
    if magicOK:
        # Word array to convert 4 bytes to a 32-bit number
        word = [1, 2**8, 2**16, 2**24]

        # Initialize the pointer index
        idX = 0

        # Read the header
        magicNumber = byteBuffer[idX : idX + 8]
        idX += 8
        version = format(np.matmul(byteBuffer[idX : idX + 4], word), "x")
        idX += 4
        totalPacketLen = np.matmul(byteBuffer[idX : idX + 4], word)
        idX += 4
        platform = format(np.matmul(byteBuffer[idX : idX + 4], word), "x")
        idX += 4
        frameNumber = np.matmul(byteBuffer[idX : idX + 4], word)
        idX += 4
        timeCpuCycles = np.matmul(byteBuffer[idX : idX + 4], word)
        idX += 4
        numDetectedObj = np.matmul(byteBuffer[idX : idX + 4], word)
        idX += 4
        numTLVs = np.matmul(byteBuffer[idX : idX + 4], word)
        idX += 4
        subFrameNumber = np.matmul(byteBuffer[idX : idX + 4], word)
        idX += 4

        # Read the TLV messages
        for tlvIdx in range(numTLVs):
            # Word array to convert 4 bytes to a 32-bit number
            word = [1, 2**8, 2**16, 2**24]

            # Check the header of the TLV message
            tlv_type = np.matmul(byteBuffer[idX : idX + 4], word)
            idX += 4
            tlv_length = np.matmul(byteBuffer[idX : idX + 4], word)
            idX += 4

            # Read the data depending on the TLV message
            if tlv_type == MMWDEMO_UART_MSG_DETECTED_POINTS:
                # Initialize the arrays
                x = np.zeros(numDetectedObj, dtype=np.float32)
                y = np.zeros(numDetectedObj, dtype=np.float32)
                z = np.zeros(numDetectedObj, dtype=np.float32)
                velocity = np.zeros(numDetectedObj, dtype=np.float32)

                for objectNum in range(numDetectedObj):
                    # Read the data for each object
                    x[objectNum] = byteBuffer[idX : idX + 4].view(dtype=np.float32)
                    idX += 4
                    y[objectNum] = byteBuffer[idX : idX + 4].view(dtype=np.float32)
                    idX += 4
                    z[objectNum] = byteBuffer[idX : idX + 4].view(dtype=np.float32)
                    idX += 4
                    velocity[objectNum] = byteBuffer[idX : idX + 4].view(
                        dtype=np.float32
                    )
                    idX += 4

                # Store the data in the detObj dictionary
                detObj = {
                    "numObj": numDetectedObj,
                    "x": x,
                    "y": y,
                    "z": z,
                    "velocity": velocity,
                }
                dataOK = 1

        # Remove already processed data
        if idX > 0 and byteBufferLength > idX:
            shiftSize = totalPacketLen

            byteBuffer[: byteBufferLength - shiftSize] = byteBuffer[
                shiftSize:byteBufferLength
            ]
            byteBuffer[byteBufferLength - shiftSize :] = np.zeros(
                len(byteBuffer[byteBufferLength - shiftSize :]), dtype="uint8"
            )
            byteBufferLength = byteBufferLength - shiftSize

            # Ensure no errors with the buffer length
            if byteBufferLength < 0:
                byteBufferLength = 0

    return dataOK, frameNumber, detObj
