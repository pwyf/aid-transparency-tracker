from iatidataquality import models, db, DATA_STORAGE_DIR, dqruntests

def run():
    taskid = dqruntests.start_testing()
    print "Running, your task id is " + str(taskid)

if __name__ == '__main__':
    run()
