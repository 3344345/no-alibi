from datetime import datetime, timedelta
from typing import List, Dict, Any
from domain.case import Case
from contracts.command import Command, Attempt
import uuid

class Scheduler:
    @classmethod
    def tick(cls, current_time: datetime, cases: List[Case], projection: Dict[str, Any]) -> List[Command]:
        generated_commands = []
        new_time = current_time + timedelta(days=30)
        
        # 1. 原有的 Case 检查逻辑
        for case in cases:
            if case.state == "resolved": continue
            if case.next_check_time and current_time >= case.next_check_time:
                generated_commands.append(Command(
                    command_id=str(uuid.uuid4()), source="scheduler", actor_id="system",
                    expected_revision=projection.get("revision", 0), world_time=new_time,
                    intent_text=f"时间到期：检查 Case {case.case_id}",
                    attempts=[Attempt(attempt_id=str(uuid.uuid4()), type="evaluate_case", target_id=case.case_id)]
                ))
                
        # 2. 模拟官场人事变动（每3个月出现一次岗位空缺考察）
        if current_time.month in [3, 6, 9, 12]:
            generated_commands.append(Command(
                command_id=str(uuid.uuid4()), source="scheduler", actor_id="system",
                expected_revision=projection.get("revision", 0), world_time=new_time,
                intent_text="季末干部调整：考察副厅级空缺",
                attempts=[Attempt(attempt_id=str(uuid.uuid4()), type="evaluate_vacancy", target_id="vice_mayor_spot")]
            ))
            
        return generated_commands