pipeline {
    agent any

    environment {
        PYTHON = 'C:\\Users\\dimcg\\AppData\\Local\\Microsoft\\WindowsApps\\python.exe'
    }

    stages {

        stage('Clonar repositorio') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/CristianMurguia/AppEncuestas.git'
            }
        }

        stage('Instalar dependencias') {
            steps {
                bat '"%PYTHON%" -m pip install django'
            }
        }

        stage('Verificar errores Django') {
            steps {
                bat '"%PYTHON%" manage.py check'
            }
        }

        stage('Correr tests') {
            steps {
                bat '"%PYTHON%" manage.py test surveys --verbosity=2'
            }
        }

    }

    post {
        success {
            echo 'Todo OK - Sin errores'
        }
        failure {
            echo 'FALLO - Revisa los errores arriba'
        }
    }
}