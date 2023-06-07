from utils import seek_process
import logging


def main():
    logging.basicConfig(filename='demo.log',
                        level=logging.WARNING,
                        format='%(asctime)s - %(name)s - %(threadName)s -  %(levelname)s - %(message)s')
    logging.info('Started')
    seek_process()
    logging.info('Finished')


if __name__ == '__main__':
    main()
