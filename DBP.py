import cx_Oracle
import csv
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import datetime

# 필요한 모듈, 오라클 설치 (테스트 불가)
try:
    from PyQt5.QtWidgets import QApplication, QLabel
except ImportError:
    print("PyQt5가 설치되어 있지 않습니다. 설치 중...")
    # PyQt5를 설치하는 코드
    subprocess.call(["pip", "install", "PyQt5"])
try:
    import cx_Oracle
except ImportError:
    print("cx_Oracle이 설치되어 있지 않습니다. 설치 중...")
    # cx_Oracle을 설치하는 코드
    subprocess.call(["pip", "install", "cx_Oracle"])

# 실행 가능한 프로그램 실행

class Scenario:
    def __init__(self, scenario_id, title, description, category, created_date):
        self.scenario_id = scenario_id
        self.title = title
        self.description = description
        self.category = category
        self.created_date = created_date

class ScenarioInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('시나리오 입력')
        self.initUI()

    def initUI(self):
        self.title_label = QLabel('제목: ')
        self.title_edit = QLineEdit()
        self.description_label = QLabel('설명: ')
        self.description_edit = QTextEdit()
        self.category_label = QLabel('카테고리: ')
        self.category_edit = QLineEdit()

        hbox = QHBoxLayout()  # hbox를 이 부분에 선언
        #self.exportBtn = QPushButton('내보내기', self)
        #hbox.addWidget(self.exportBtn)

        self.okBtn = QPushButton('확인', self)
        self.cancelBtn = QPushButton('취소', self)

        hbox.addWidget(self.okBtn)
        hbox.addWidget(self.cancelBtn)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.title_label)
        vbox.addWidget(self.title_edit)
        vbox.addWidget(self.description_label)
        vbox.addWidget(self.description_edit)
        vbox.addWidget(self.category_label)
        vbox.addWidget(self.category_edit)
        vbox.addLayout(hbox)

        self.okBtn.clicked.connect(self.accept)
        self.cancelBtn.clicked.connect(self.reject)


    def getScenarioInfo(self):
        return {
            'title': self.title_edit.text(),
            'description': self.description_edit.toPlainText(),
            'category': self.category_edit.text()
        }
    
    def setScenarioInfo(self, scenario_info):
        self.title_edit.setText(scenario_info['title'])

        # cx_Oracle.LOB를 문자열로 변환
        description_text = str(scenario_info['description'].read()) if scenario_info['description'] else ""
        self.description_edit.setPlainText(description_text)

        self.category_edit.setText(scenario_info['category'])
        
class MainScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.exportBtn = QPushButton('내보내기', self)  # exportBtn을 클래스 멤버로 선언
        self.importBtn = QPushButton('가져오기', self)  # importBtn을 클래스 멤버로 선언
        self.initUI()
        self.connectToOracle()
        self.loadScenarioData()

    def initUI(self):
        self.setWindowTitle('시나리오 관리 시스템')
        self.resize(1280, 760)

        # 버튼
        self.createBtn = QPushButton('생성', self)
        self.editBtn = QPushButton('편집', self)
        self.deleteBtn = QPushButton('삭제', self)

        # 시나리오 목록 표시
        self.scenarioListWidget = QListWidget()

        # 레이아웃
        vbox = QVBoxLayout(self)

        hbox = QHBoxLayout()
        hbox.addWidget(self.createBtn)
        hbox.addWidget(self.editBtn)
        hbox.addWidget(self.deleteBtn)
        hbox.addWidget(self.exportBtn)
        hbox.addWidget(self.importBtn)
        vbox.addLayout(hbox)

        vbox.addWidget(self.scenarioListWidget)

        # 버튼 클릭 이벤트
        self.createBtn.clicked.connect(self.createScenario)
        self.editBtn.clicked.connect(self.editScenario)
        self.deleteBtn.clicked.connect(self.deleteScenario)
        self.exportBtn.clicked.connect(self.exportScenario)
        self.importBtn.clicked.connect(self.importScenario)

        # 시나리오 목록 더블클릭 이벤트
        self.scenarioListWidget.itemDoubleClicked.connect(self.showScenarioDetails)

    
    def showScenarioDetails(self, item):
        selected_scenario = item.data(Qt.UserRole)

        # 선택한 시나리오의 세부 정보를 새 창에 표시
        details_dialog = ScenarioDetailsDialog(selected_scenario, parent=self)
        details_dialog.exec_()

    def connectToOracle(self):
        try:
            connection = cx_Oracle.connect("SYSTEM", "12321", "localhost:1521/XE", encoding="UTF-8")
            # 커서
            self.cursor = connection.cursor()
        except cx_Oracle.Error as e:
            print(e)
            
    def loadScenarioData(self):
        # 데이터베이스에서 시나리오 데이터 불러와서 리스트화
        try:
            self.cursor.execute("SELECT * FROM SCENARIO")
            rows = self.cursor.fetchall()
        
            self.scenarioList = []
            for row in rows:
                scenario = Scenario(*row)
                self.scenarioList.append(scenario)
    
            self.updateScenarioListWidget()
        except cx_Oracle.Error as e:
            print(e)


    def createScenario(self):
        input_dialog = ScenarioInputDialog(self)
        if input_dialog.exec_() == QDialog.Accepted:
            scenario_info = input_dialog.getScenarioInfo()
            if scenario_info['title'].strip():
                created_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # 데이터베이스에 시나리오 데이터 저장
                self.cursor.execute("""
                    INSERT INTO SCENARIO (SCENARIOID, TITLE, DESCRIPTION, CATEGORY, CREATEDDATE)
                    VALUES (SCENARIO_SEQ.NEXTVAL, :title, :description, :category, TO_TIMESTAMP(:created_date, 'YYYY-MM-DD HH24:MI:SS'))
                """, title=scenario_info['title'], description=scenario_info['description'], category=scenario_info['category'], created_date=created_date)

                self.loadScenarioData()

    def editScenario(self):
        selected_item = self.scenarioListWidget.currentItem()
        if selected_item:
            input_dialog = ScenarioInputDialog(self)
    
            # 선택한 시나리오의 정보를 가져와서 대화상자에 설정
            selected_scenario = selected_item.data(Qt.UserRole)
            input_dialog.setScenarioInfo({
                'title': selected_scenario.title,
                'description': selected_scenario.description,
                'category': selected_scenario.category
            })
    
            if input_dialog.exec_() == QDialog.Accepted:
                scenario_info = input_dialog.getScenarioInfo()
                if scenario_info['title'].strip():
                    # 데이터베이스에서 시나리오 데이터 업데이트
                    self.cursor.execute("""
                        UPDATE SCENARIO
                        SET TITLE = :title, DESCRIPTION = :description, CATEGORY = :category
                        WHERE SCENARIOID = :scenario_id
                    """, title=scenario_info['title'], description=scenario_info['description'], category=scenario_info['category'], scenario_id=selected_scenario.scenario_id)

                    self.loadScenarioData()

    def deleteScenario(self):
        selected_item = self.scenarioListWidget.currentItem()
        if selected_item:
            selected_scenario = selected_item.data(Qt.UserRole)

            # 데이터베이스에서 시나리오 데이터 삭제
            self.cursor.execute("DELETE FROM SCENARIO WHERE SCENARIOID = :scenario_id", scenario_id=selected_scenario.scenario_id)

            self.loadScenarioData()
            
    # 사용자가 테이블에서 특정 시나리오를 클릭했을 때
    def showScenarioInfo(self, item):
        # 선택한 시나리오 정보 표시
        selected_scenario = item.data(Qt.UserRole)
        self.title_edit.setText(selected_scenario.title)
        self.description_edit.setText(selected_scenario.description)
        self.category_edit.setText(selected_scenario.category)
    
    def __del__(self):
        # 객체 소멸 시 데이터베이스 연결 종료
        self.cursor.close()

    def updateScenarioListWidget(self):
        # 시나리오 목록 업데이트
        self.scenarioListWidget.clear()
        for scenario in self.scenarioList:
            item = QListWidgetItem(scenario.title)
            item.setData(Qt.UserRole, scenario)
            self.scenarioListWidget.addItem(item)
            
    def exportScenario(self):
        # 모든 시나리오와 관련된 데이터를 CSV 파일로 내보내기
        filename, _ = QFileDialog.getSaveFileName(self, 'CSV로 내보내기', '', 'CSV 파일 (*.csv)')
    
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    csv_writer = csv.writer(csvfile)
    
                    # 시나리오 정보 헤더
                    csv_writer.writerow(['Scenario ID', 'Title', 'Description', 'Category', 'Created Date'])
    
                    # 모든 시나리오 레코드 내보내기
                    for scenario in self.scenarioList:
                        csv_writer.writerow([scenario.scenario_id, scenario.title, scenario.description, scenario.category, scenario.created_date])
    
                    QMessageBox.information(self, '내보내기 완료', '모든 시나리오가 성공적으로 내보내졌습니다.')
            except Exception as e:
                QMessageBox.critical(self, '오류', f'내보내기 중 오류가 발생했습니다: {str(e)}')
                
    def importScenario(self):
        # CSV 파일 선택 다이얼로그 표시
        filename, _ = QFileDialog.getOpenFileName(self, 'CSV에서 가져오기', '', 'CSV 파일 (*.csv)')
    
        if filename:
            try:
                with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                    csv_reader = csv.reader(csvfile)
                    header = next(csv_reader)  # 헤더 스킵
    
                    # 모든 시나리오 정보 읽기
                    for scenario_data in csv_reader:
                        print(f"Importing scenario: {scenario_data}")  # 디버깅 출력 추가
                        # 데이터베이스에 시나리오 정보 추가
                        self.cursor.execute("""
                            INSERT INTO SCENARIO (SCENARIOID, TITLE, DESCRIPTION, CATEGORY, CREATEDDATE)
                            VALUES (:scenario_id, :title, :description, :category, TO_TIMESTAMP(:created_date, 'YYYY-MM-DD HH24:MI:SS'))
                        """, scenario_id=scenario_data[0], title=scenario_data[1], description=scenario_data[2],
                                          category=scenario_data[3], created_date=scenario_data[4])
    
                self.loadScenarioData()
                QMessageBox.information(self, '가져오기 완료', '시나리오가 성공적으로 가져와졌습니다.')
            except Exception as e:
                print(e)  # 콘솔에 오류 출력
                QMessageBox.critical(self, '오류', f'가져오기 중 오류가 발생했습니다: {str(e)}')

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    myApp = MainScreen()
    myApp.show()
    
    # 종료
    app.setQuitOnLastWindowClosed(True)
    sys.exit(app.exec_())