def remote = [:]
remote.name = "silo"
remote.host = "silo.mskcc.org"
remote.allowAnyHosts = true

pipeline {
  agent any

  stages {
    stage('Logging into Server') {
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'fc553c62-8e84-4a2c-b012-db1b9c58195d', keyFileVariable: 'SSH_KEY', passphraseVariable: 'PASSPHRASE', usernameVariable: 'USER_NAME')]){

                remote.user = USER_NAME
                remote.identityFile = SSH_KEY
                stage("SSH Steps") {

                    sshScript remote: remote, script: '/home/pankeyd/scripts/hello.sh'

         }
       }
     }
   }
 }
}
