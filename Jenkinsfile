pipeline {
  agent any

  stages {
    stage('Logging into Server') {
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'fc553c62-8e84-4a2c-b012-db1b9c58195d', keyFileVariable: 'SSH_KEY', passphraseVariable: 'PASSPHRASE', usernameVariable: 'USER_NAME')]) {

          sh '/home/pankeyd/scripts/hello.sh'

        }
      }
    }
