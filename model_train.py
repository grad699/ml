import pandas as pd
from app_logging.logging import get_logs
from training_validation.train_validation  import Validations
from preprocessing.data_preprocessing import preprocess
from preprocessing.clustering import Create_Clusters
from model_selection.best_model_finder import FindBestModel
import json
from database_insertion.database_operartions import DBOperations
import os
import shutil


global X, y, full_data, clustered_X
class Trainer:
    def __init__(self):
        self.valid_classObj = Validations()
        self.logger = get_logs( open("logs//Training_dataIngestion_validation_logs.txt" , 'a'))
        self.logger.write_logs("Entered Trainer Class.")



    def Training_Validations(self):
        """
        Method Name : Training_Validations
        Description : This method is written to apply Validations on the given batch files in terms of
                        valid data, valid columns, fileName etc.
                      If the TrainingBatchFile is valid then it is returned successfully from the function.
                      else : It is moved to 'BadDataFolder' .
        Returns : Valid_BatchFiles

        """
        self.logger.write_logs("Entered Training_Validations method in Trainer class.")
        name = self.valid_classObj.getTrainingBatchFiles()
        #print(name)

        valid_BatchFiles = []
        for i in name:
            print(self.valid_classObj.matchRegularExpression(i))


            if (self.valid_classObj.CheckColumn_Name_Numbers(i) and \
                self.valid_classObj.CheckColumnDatatype(i)) and\
                    self.valid_classObj.matchRegularExpression(i):
                valid_BatchFiles.append(i)

        #print(valid_BatchFiles)
        self.logger.write_logs(f"Here valid BatchFileNames : {valid_BatchFiles}")
        self.logger.write_logs(f"Here invalid BatchFileNames : {set(name).difference(valid_BatchFiles)}")


        if list(set(name).difference(valid_BatchFiles)) != []:
            self.logger.write_logs(f"Moving Invalid Training Batch Files to BadDataFolder")
            for InvalidBatchFile in list(set(name).difference(valid_BatchFiles)):
                shutil.move(os.path.join(os.getcwd() , "Training_BatchFiles" , InvalidBatchFile) ,os.path.join(os.getcwd() , "BadDataFolder" , InvalidBatchFile) )


        self.logger.write_logs("Existing from Training_Validations method.")

        return valid_BatchFiles

    def Preprocessing_clustering(self, full_data):
        """
        Method Name : Preprocessing_clustering
        Description : This method is written to apply entire preprocessing and clustering part on the given full data.
                      This includes Seprating Feaure and Target column fro mthe full data , Scale the data,
                      Create optimum clusters form the data.

        Parameters : full_data : Full raw Data

        """
        self.logger.write_logs("Entered Preprocessing_clustering method in Trainer class.")

        data_processor = preprocess()
        self.X , self.y = data_processor.separate_X_Y(full_data)
        self.columns = list(self.X.columns)
        # X = data_processor.Data_Imputation(X)
        self.X = pd.DataFrame(data_processor.scaling(self.X) , columns = self.columns)

        clustering = Create_Clusters()
        self.clustered_X = clustering.Create_Clusters_From_Data(self.X , clustering.silhoutte_score(self.X)[0] )


    def training_clusterd_data(self):
        """
        Method Name : training_clusterd_data
        Description : This method is written to train different created clusters from the data with
                      optimal parameters which gives the maximum accuracy.

        """
        n = self.clustered_X['cluster'].max()
        RF_grid = {'n_estimators': [125, 150, 200, 300, 400], "criterion": ['squared_error']}
        XG_grid = {'learning_rate': [0.01, 0.05, 0.1, 0.17, 0.3], 'gamma': [0.1, 0.2, 0.4],
                   'min_child_weight': [1, 5, 10]}


        for cluster_number in range(n):
            find_best_model_for_clusters = FindBestModel(self.clustered_X[ self.clustered_X['cluster'] == cluster_number ].drop("cluster" , axis=1) , \
                                                         self.y.iloc[  list(self.clustered_X[ self.clustered_X['cluster'] == cluster_number ].index) , : ] , str(cluster_number) )
            find_best_model_for_clusters.best_model(XG_grid , RF_grid)


    def Get_TriningBatchData(self):
        """
        Method Name : Get_TriningBatchData
        Description : This method is written to get all Training Batch Files in the folder 'Training_BatchFiles'.
                      And dumps the integrated full data from the BatchFiles into the database.
                      This is a part of DataIngestion.

        """
        Valid_dataFiles = self.Training_Validations()

        with open("schema_training.json", "r") as read_it:
            self.schemaTraining_json = json.load(read_it)

        columns = list(self.schemaTraining_json['ColName'].keys())

        finalTraining_df = pd.DataFrame(columns=columns)

        for datafile in Valid_dataFiles:
            df = pd.read_csv("Training_BatchFiles//"+datafile)
            finalTraining_df = pd.concat([finalTraining_df , df] , axis=0)

        database = DBOperations()
        database.Dataframetodatabase(finalTraining_df)





