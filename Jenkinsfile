
pipeline {
  agent any

  stages {
      stage("SSH Steps") {
        steps{

          withCredentials([sshUserPrivateKey(credentialsId: 'fc553c62-8e84-4a2c-b012-db1b9c58195d', keyFileVariable: 'identity', passphraseVariable: 'passphrase', usernameVariable: 'userName')]) {

          sh ‘ssh pankeyd@silo.mskcc.org whoami’


        }



    }
    }
  }
}
