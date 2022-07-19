pipeline {
  agent any
  parameters {
      choice(name: 'SERVER', choices: ['DEV', 'STAGE','PROD'], description: 'Server')

     }
  stages {
      stage("Deploy to Dev") {
      when {
      expression { params.SERVER == 'DEV' }
    }
    stages{
      stage ("Update Config File"){
      steps {
sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cp -p /srv/services/beagle_dev/beagle/env_beagle_1.sh /srv/services/beagle_dev/beagle/config_backups/config_$(date +"%m-%d-%y-%T").sh"'

configFileProvider(
[configFile(fileId: '32ce55fe-3948-4fca-92c4-1b5d6ace9a3f', variable: 'CONFIG_FILE_DEV')]) {
sh 'chmod 755 $CONFIG_FILE_DEV'
sh 'mv $CONFIG_FILE_DEV $CONFIG_FILE_DEV.sh'
sh 'scp -p -o StrictHostKeyChecking=no $CONFIG_FILE_DEV.sh voyager@silo.mskcc.org:/srv/services/beagle_dev/beagle/env_beagle_1.sh'
sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd /srv/services/beagle_dev/beagle && source run_restart.sh"'

}
}
}
      }
      stage("Deployment"){
      steps {
        echo "deply to dev"
           sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
            sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd /srv/services/beagle_dev/beagle && git checkout $BRANCH_NAME && git pull && source run_restart.sh"'

          }

        }
        }
        }
      }
      stage('Deploy to Stage') {
      when {
      expression { params.SERVER == 'STAGE' }
    }
    stages{
          stage("Update Stage Config File"){
          steps {
      sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
      sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cp -p /srv/services/staging_voyager/beagle/env_beagle.sh /srv/services/staging_voyager/beagle/config_backups/config_$(date +"%m-%d-%y-%T").sh"'

      configFileProvider(
      [configFile(fileId: 'dbd63d24-a881-4309-befb-b3501f98662d', variable: 'CONFIG_FILE_STAGE')]) {
      sh 'chmod 755 $CONFIG_FILE_STAGE'
      sh 'mv $CONFIG_FILE_STAGE $CONFIG_FILE_STAGE.sh'
      sh 'scp -p -o StrictHostKeyChecking=no $CONFIG_FILE_STAGE.sh voyager@silo.mskcc.org:/srv/services/staging_voyager/beagle/env_beagle.sh'
      sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd /srv/services/staging_voyager/beagle && source run_restart.sh"'

   }
  }
    }
          }
          stage("Stage Deployment"){
            steps {
              echo "deply to stage"
            /*  sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
              sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd /srv/services/beagle_dev/beagle && git checkout $BRANCH_NAME && git pull && source run_restart.sh"'

             }*/
              }
              }
              }
          }
          stage('Deploy to Prod') {
          when {
          expression { params.SERVER == 'PROD' }
        }
        stages{
        stage("Update Prod Config file"){
        steps {
      sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {

      sh 'ssh  -o StrictHostKeyChecking=no  voyager@voyager.mskcc.org "cp -p /srv/services/beagle/config/config.sh /srv/services/beagle/config_backups/config_$(date +"%m-%d-%y-%T").sh"'

      configFileProvider(
      [configFile(fileId: 'd7b82e90-6c47-4228-a237-ae23d85bbd68', variable: 'CONFIG_FILE_PROD')]) {
      sh 'chmod 755 $CONFIG_FILE_PROD'
      sh 'mv $CONFIG_FILE_PROD $CONFIG_FILE_PROD.sh'
      sh 'scp -p -o StrictHostKeyChecking=no $CONFIG_FILE_PROD.sh voyager@voyager.mskcc.org:/srv/services/beagle/config/config.sh'
      sh 'ssh  -o StrictHostKeyChecking=no  voyager@voyager.mskcc.org "cd /srv/services/beagle && source run_restart.sh"'

   }
  }
    }

        }
          stage("Prod Deployment"){
                steps {
                  echo "deply to PROD"
                /*  sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
                   sh 'ssh  -o StrictHostKeyChecking=no  voyager@voyager.mskcc.org "cd /srv/services/beagle/code/beagle && git checkout $BRANCH_NAME && git pull && source run_restart.sh"'

                 } */
                  }
                  }
                  }
              }
  }
}
