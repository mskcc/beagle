pipeline {
  agent any

  triggers {
  pollSCM('') // Enabling being build on Push

  }
  stages {
    stage("Deploy") {
      steps {
        sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
          sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd /srv/services/beagle_dev/beagle && git checkout develop && git pull && source run_restart.sh"'
        //sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org cd /srv/services/staging_voyager/beagle'

        }

      }
    }
  }
}
//
