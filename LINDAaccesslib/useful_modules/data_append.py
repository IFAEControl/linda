import pandas as pd
import numpy as np
import queue, os


def append_data_to_csv(q, doc_path, shell):
    """
    Appends data to a csv file.

    :param q: Queue object. (object)
    :param doc_path: Absolute path. (str)
    :param shell: Shell object to display info on logg. (object)
    """
    dacx_data = []
    dacy_data = []
    dacz_data = []
    dacx = None
    dacy = None
    dacz = None

    while True:
        try:
            item, dac1, dac2, dac3 = q.get(timeout=2)
            dacx = dac1
            dacy = dac2
            dacz = dac3

            dacx_data.append(item[dacx])
            dacy_data.append(item[dacy])
            dacz_data.append(item[dacz])

            q.task_done()
        except queue.Empty:
            shell.info("All data added correctly")
            break

    try:
        dacx_data = np.reshape(dacx_data, (len(dacx_data) * len(dacx_data[0]), len(dacx_data[0][0])))
        dacy_data = np.reshape(dacy_data, (len(dacy_data) * len(dacy_data[0]), len(dacy_data[0][0])))
        dacz_data = np.reshape(dacz_data, (len(dacz_data) * len(dacz_data[0]), len(dacz_data[0][0])))

        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') + "\\"

        df = pd.DataFrame(dacx_data)
        df.to_csv(doc_path + f"_DAC{dacx}.txt", index_label=False, header=False, index=False)

        try:
            df.to_csv(desktop + f"LAST_DAC{dacx}_IMAGE.csv", index_label=False, header=False, index=False)
        except:
            shell.error(f"{desktop}LAST_DAC{dacx}_IMAGE.csv")

        df = pd.DataFrame(dacy_data)
        df.to_csv(doc_path + f"_DAC{dacy}.txt", index_label=False, header=False, index=False)

        try:
            df = pd.DataFrame(dacy_data)
            df.to_csv(desktop + f"LAST_DAC{dacy}_IMAGE.csv", index_label=False, header=False, index=False)
        except:
            shell.error(f"{desktop}LAST_DAC{dacy}_IMAGE.csv")

        df = pd.DataFrame(dacz_data)
        df.to_csv(doc_path + f"_DAC{dacz}.txt", index_label=False, header=False, index=False)

        try:
            df = pd.DataFrame(dacz_data)
            df.to_csv(desktop + f"LAST_DAC{dacz}_IMAGE.csv", index_label=False, header=False, index=False)
        except:
            shell.error(f"{desktop}LAST_DAC{dacz}_IMAGE.csv")

        shell.info("File correctly written!")

    except FileNotFoundError:
        shell.error("File not found")
