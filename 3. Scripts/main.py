import utils
import logging


def main():
    logging.basicConfig(filename='demo.log',
                        level=logging.WARNING,
                        format='%(asctime)s - %(name)s - %(threadName)s -  %(levelname)s - %(message)s')
    logging.info('Started')
    #utils.job_info_process()
    logging.info('Completed job info search')
    utils.job_details_process()
    logging.info('Finished')


if __name__ == '__main__':
    main()

