DB백업파일 가져오기 (DB 사용자 생성 필요)

(sqlplus "/as sysdba")
-- 새로운 사용자 만들기
create user c##myid identified by 0000;
-- 권한 부여
grant connect, resource, dba to c##myid;

cmd
-- db 임포트
imp userid=SYSTEM/0000 FROMUSER=system TOUSER=c##myid FILE=F:\공부\DBP\backup.dump
