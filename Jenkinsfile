def remote = [:]
remote.name = "silo.mskcc.org"
remote.host = "silo.mskcc.org"
remote.allowAnyHosts = true
pipeline {

  stages {
    node{
    withCredentials([sshUserPrivateKey(credentialsId: 'fc553c62-8e84-4a2c-b012-db1b9c58195d', keyFileVariable: 'identity', passphraseVariable: 'passphrase', usernameVariable: 'userName')]) {
        remote.user = userName
        remote.identityFile = identity
        stage("SSH Steps") {

          sshCommand remote: remote, command: 'whoami'

            }

          }

       }

   }
}
