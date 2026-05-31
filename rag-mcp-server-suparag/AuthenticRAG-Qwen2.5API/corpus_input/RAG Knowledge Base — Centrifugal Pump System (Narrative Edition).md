# RAG Knowledge Base — Centrifugal Pump System
### เอกสารสำหรับ AI Agent ระบบ Prescriptive Maintenance
**อุปกรณ์อ้างอิง:** Centrifugal Pump (ปั๊มหอยโข่ง) แบบแนวนอน (Horizontal End-Suction)
**ใช้งานกับ:** Node-RED Sensor Simulation → MCP Server → AI Agent + RAG

***
## ฉบับที่ 1 — คู่มือการทำงานและค่าพารามิเตอร์มาตรฐาน (Equipment Manual)
ปั๊มหอยโข่ง (Centrifugal Pump) แบบแนวนอนในระบบนี้ออกแบบมาเพื่อสูบของเหลวอุณหภูมิปกติในกระบวนการผลิต การทำความเข้าใจค่าพารามิเตอร์ปกติของแต่ละ Sensor เป็นสิ่งจำเป็นสำหรับ AI Agent เพื่อตีความสัญญาณที่ได้รับว่าควรดำเนินการอย่างไร

**อุณหภูมิ (Temperature)** เป็นตัวชี้วัดสุขภาพของ Bearing และของเหลวในระบบ ในสภาวะปกติ อุณหภูมิที่ Bearing Housing ไม่ควรเกิน 70 องศาเซลเซียส ตราบเท่าที่ค่ายังอยู่ต่ำกว่านี้ถือว่าระบบทำงานเป็นปกติ เมื่ออุณหภูมิเพิ่มขึ้นเข้าสู่ช่วง 70 ถึง 80 องศา นั่นคือสัญญาณเตือนว่าอาจมีแรงเสียดทานผิดปกติเกิดขึ้นภายใน ควรแจ้งทีม Maintenance ให้เข้าตรวจสอบโดยเร็ว หากอุณหภูมิขยับเกิน 80 องศา ถือว่าวิกฤต และหากพุ่งเกิน 95 องศา ต้องหยุดเครื่องทันทีเพราะ Bearing อาจเสียหายถาวรได้ ทั้งนี้ ถ้าอุณหภูมิแวดล้อมในโรงงานสูงกว่า 40 องศา ให้ปรับ Threshold ขึ้นตามสัดส่วนด้วย[^1][^2][^3]

**แรงดัน (Pressure)** สะท้อนสภาพของ Impeller และระบบท่อโดยตรง แรงดันที่ Discharge ในสภาวะปกติอยู่ระหว่าง 2.0 ถึง 4.0 บาร์ ถ้าแรงดันลดลงมาอยู่ในช่วง 1.5 ถึง 2.0 บาร์ อาจเป็นสัญญาณของการรั่ว หรือ Impeller เริ่มสึกหรอ และถ้าต่ำกว่า 1.5 บาร์ ระบบเสี่ยงต่อปรากฏการณ์ Cavitation ซึ่งเกิดจากฟองอากาศที่ก่อตัวและยุบตัวภายในปั๊ม สามารถทำลาย Impeller ได้อย่างรวดเร็ว ในทางตรงข้าม ถ้าแรงดันสูงเกิน 5.0 บาร์ ให้หยุดเครื่องทันทีเพราะ Mechanical Seal และ Casing อาจทนแรงดันนั้นไม่ไหว[^4][^5]

**อัตราการไหล (Flow Rate)** บอกให้รู้ว่าปั๊มส่งของเหลวได้ตามที่ออกแบบไว้หรือไม่ ค่าปกติอยู่ระหว่าง 80 ถึง 120 ลิตรต่อนาที การลดลงมาอยู่ที่ 50 ถึง 80 ลิตรต่อนาทีอาจบ่งชี้ถึงการอุดตันบางส่วน และถ้าต่ำกว่า 50 ลิตรต่อนาที ปั๊มเสี่ยงต่อภาวะ Dry Running ซึ่งหมายความว่าปั๊มหมุนโดยไม่มีของเหลวหล่อเลี้ยง ทำให้ Mechanical Seal และ Bearing ร้อนจัดและเสียหายอย่างรวดเร็ว สิ่งสำคัญที่ต้องเข้าใจคือ Flow Rate ของปั๊มหอยโข่งไม่ได้เป็นสัดส่วนโดยตรงกับความเร็วรอบเสมอไป เพราะขึ้นอยู่กับจุดตัดระหว่าง Pump Curve และ System Curve ด้วย[^6][^7][^8]

**ความเร็วรอบมอเตอร์ (Motor Speed)** สำหรับมอเตอร์ 4-pole ที่ใช้กับระบบไฟ 50 เฮิร์ตซ์ ค่าปกติอยู่ระหว่าง 1,400 ถึง 1,500 รอบต่อนาที ถ้าต่ำกว่า 1,200 รอบต่อนาทีโดยไม่ได้ตั้งค่า VFD ให้ต่ำ แสดงว่ามอเตอร์รับโหลดหนักเกินหรืออาจมีการยึดติดทางกลไก และถ้าความเร็วเกิน 1,600 รอบต่อนาที อาจเกิดความเสียหายทางกลไกที่ Shaft และ Bearing ได้

**สถานะปั๊ม (Pump Status)** มีอยู่ด้วยกัน 5 สถานะ ได้แก่ RUNNING คือทำงานปกติ, IDLE คือสแตนด์บาย, STARTING คือกำลังติดเครื่องและยังไม่ถึง Steady State ซึ่งในช่วงนี้ AI Agent ไม่ควรตัดสินค่า Sensor เพราะค่าจะผันผวนใน 30 วินาทีแรก, STOPPING คือกำลังหยุด และ FAULT คือระบบตรวจพบข้อผิดพลาดและต้องการการวินิจฉัยทันที

สิ่งสำคัญที่ AI Agent ต้องเรียนรู้คือการตีความค่า Sensor หลายตัวพร้อมกัน ไม่ใช่มองทีละค่า ตัวอย่างเช่น เมื่อแรงดันต่ำและ Flow Rate ต่ำในเวลาเดียวกัน สาเหตุแรกที่ต้องสงสัยคือการอุดตันที่ Suction Side หรือ Cavitation ไม่ใช่ Impeller สึก แต่ถ้าอุณหภูมิสูงโดยที่ Flow Rate ปกติ สาเหตุที่เป็นไปได้มากกว่าคือปัญหาที่ Bearing ไม่ใช่ปัญหาของระบบไหล และถ้าความเร็วรอบปกติแต่ Flow Rate และแรงดันต่ำพร้อมกัน มักหมายถึง Impeller สึกหรือมีอากาศอยู่ใน Suction Line[^5][^4]

***
## ฉบับที่ 2 — คู่มือวินิจฉัยและแก้ไข Alarm (Troubleshooting Guide)
เอกสารนี้ช่วยให้ AI Agent วินิจฉัยสาเหตุของความผิดปกติและเสนอขั้นตอนแก้ไขได้อย่างถูกต้องและมีบริบท แต่ละสถานการณ์เขียนอธิบายเชิงลึกเพื่อให้เข้าใจว่า "ทำไม" ไม่ใช่แค่ "ต้องทำอะไร"
### ปั๊มไม่สูบน้ำทั้งที่สถานะเป็น RUNNING
เมื่อระบบบอกว่าปั๊มทำงานอยู่ แต่ Flow Rate เป็นศูนย์หรือต่ำกว่า 10 ลิตรต่อนาที และแรงดันก็เป็นศูนย์ด้วย ปัญหาแรกที่ต้องตรวจสอบเสมอคือการ Priming ปั๊มหอยโข่งไม่สามารถดูดน้ำได้เลยหากมีอากาศอยู่ภายในตัวปั๊มหรือใน Suction Line เพราะปั๊มชนิดนี้ไม่ได้ออกแบบมาเพื่อดูดอากาศ ให้ตรวจสอบโดยเปิด Vent Plug บนตัวปั๊ม ถ้าน้ำไหลออกมาแสดงว่าได้ทำ Prime แล้ว ถ้าอากาศพุ่งออกมาแทน ต้องเติมน้ำเข้าระบบและ Prime ใหม่[^5]

หากการ Prime ไม่ใช่ปัญหา ให้ตรวจสอบ Suction Strainer ซึ่งเป็นตะแกรงกรองที่ปากทางเข้าของปั๊ม เศษวัสดุในระบบจะสะสมที่นี่จนอุดตัน ทำให้น้ำเข้าปั๊มไม่ได้เลย ให้ถอดออกและล้างทำความสะอาด[^5]

อีกสาเหตุที่มักถูกมองข้ามในการ Commissioning ครั้งแรกหรือหลังซ่อมใหญ่คือมอเตอร์หมุนผิดทิศทาง ปั๊มหอยโข่งมีทิศการหมุนที่กำหนดไว้ ถ้ามอเตอร์ถูกต่อไฟกลับสายทำให้หมุนสวนทาง Impeller จะไม่สร้างแรงดันหรือ Flow ได้เลย ให้ตรวจสอบลูกศรบน Casing ของปั๊มว่าตรงกับทิศที่มอเตอร์หมุน และยืนยันโดยการสังเกต Coupling ขณะ Start เครื่องช่วงสั้นๆ[^5]

สุดท้ายให้ตรวจ Foot Valve ที่ปลาย Suction ถ้า Foot Valve รั่วหรือเปิดค้างไว้ น้ำจะไหลกลับลงไปทุกครั้งที่ปั๊มหยุด ทำให้ระบบ Lose Prime และต้อง Prime ใหม่ทุกครั้งที่ Start สังเกตได้โดยดู Pressure Gauge หลังปั๊มหยุด ถ้าแรงดันตกลงอย่างรวดเร็วทันทีที่หยุด มักหมายถึง Foot Valve รั่ว
### Flow Rate ต่ำกว่าปกติ
เมื่อ Flow Rate อยู่ในช่วง 50 ถึง 80 ลิตรต่อนาทีต่อเนื่องนานกว่า 5 นาที สาเหตุที่พบบ่อยที่สุดในโรงงานคือ Impeller ที่สึกหรอจากการใช้งานระยะยาว อนุภาคแข็งในของเหลว แม้จะมีขนาดเล็กมาก จะค่อยๆ กัดกร่อน Blade ของ Impeller ทีละน้อย ทำให้ประสิทธิภาพลดลงอย่างช้าๆ จนเจ้าของเครื่องมักไม่สังเกตเห็น การยืนยันต้องทำโดยเปิด Pump Casing ออกและตรวจ Impeller โดยตรง[^4][^5]

Air Leak ที่ Suction Side เป็นอีกสาเหตุที่พบบ่อยแต่วินิจฉัยได้ยาก รอยรั่วเพียงเล็กน้อยที่ Gasket หรือ Mechanical Seal ฝั่ง Suction จะดูดอากาศเข้ามาผสมกับน้ำ ทำให้ปั๊มไม่สามารถสร้าง Flow เต็มประสิทธิภาพได้ วิธีสังเกตคือดู Pressure Gauge ที่ Suction ขณะปั๊มทำงาน ถ้าค่าผันผวนขึ้นลงผิดปกติแทนที่จะนิ่ง มักบ่งชี้ว่ามีอากาศในระบบ[^5]

Impeller Clearance ที่กว้างเกินกำหนดเป็นสาเหตุที่หลายคนไม่นึกถึง ช่องว่างระหว่าง Impeller กับ Casing Liner ในมาตรฐานทั่วไปไม่ควรเกิน 0.3 ถึง 0.5 มิลลิเมตร ถ้าเกินกว่านั้น ของเหลวจะ Bypass ไหลวนกลับแทนที่จะถูกส่งออก ผลที่ได้คือ Flow ลดลงทั้งๆ ที่ RPM ยังปกติ ต้องวัดด้วย Feeler Gauge หลังถอด Casing ออก และเปลี่ยน Wear Ring เมื่อ Clearance เกิน 0.8 มิลลิเมตร[^5]
### อุณหภูมิสูงผิดปกติ
อุณหภูมิ Bearing ที่สูงเกิน 80 องศาเซลเซียสต่อเนื่องนานกว่า 3 นาทีถือเป็นสัญญาณที่ไม่ควรละเลย สาเหตุหลักในอุตสาหกรรมคือ Misalignment ระหว่างปั๊มกับมอเตอร์ เมื่อ Shaft ของทั้งสองไม่ได้ Align กันอย่างแม่นยำ แรงที่กระทำต่อ Bearing จะเพิ่มขึ้นมากกว่าที่ออกแบบไว้หลายเท่า ความร้อนที่เกิดขึ้นจึงสูงผิดปกติ การตรวจสอบต้องใช้ Dial Indicator หรือ Laser Alignment Tool วัดทั้ง Radial และ Angular Misalignment ค่าที่ยอมรับได้คือ Radial ไม่เกิน 0.05 มิลลิเมตร และ Angular ไม่เกิน 0.05 มิลลิเมตรต่อ 100 มิลลิเมตรความยาว[^5][^9]

น้ำมันหล่อลื่นไม่เพียงพอหรือเสื่อมสภาพเป็นสาเหตุที่แก้ไขได้ง่ายที่สุด ปั๊มส่วนใหญ่ใช้น้ำมัน ISO VG 46 หรือ 68 ระดับน้ำมันต้องอยู่ที่กึ่งกลาง Sight Glass เสมอ ถ้าต่ำกว่านั้นให้เติมทันที และควรเปลี่ยนน้ำมันทุก 2,000 ชั่วโมงการทำงานหรือทุก 3 เดือน เพราะน้ำมันที่ใช้งานนานจะเสื่อมสมบัติและสูญเสียความสามารถในการหล่อลื่น[^10][^11][^9]

ถ้าตรวจแล้วพบว่า Alignment ดีและน้ำมันเพียงพอ แต่อุณหภูมิยังค่อยๆ สูงขึ้นทุกวันอย่างต่อเนื่องในช่วง 1 ถึง 2 สัปดาห์ที่ผ่านมา ให้สงสัย Bearing เสื่อมเป็นอันดับแรก Bearing ที่กำลังจะเสียจะค่อยๆ สร้างความร้อนมากขึ้นเรื่อยๆ ก่อนที่จะเสียสนิท ในกรณีนี้ให้วางแผนเปลี่ยน Bearing ในรอบ Maintenance ถัดไปโดยไม่ต้องรอให้เสียก่อน[^4]
### มอเตอร์โอเวอร์โหลดและหยุดกะทันหัน
เมื่อสถานะเปลี่ยนเป็น FAULT ทันทีพร้อมกับ RPM ตก สาเหตุที่เป็นไปได้หลักๆ มีสองแบบ แบบแรกคือ Flow Rate สูงเกินค่าออกแบบ เมื่อปั๊มส่งน้ำมากกว่า Rated Flow มอเตอร์จะรับโหลดเพิ่มขึ้น ถ้าเกิดขึ้นต่อเนื่อง Overload Relay จะ Trip เพื่อปกป้องมอเตอร์ ให้ตรวจสอบ Valve Position ทุกจุดโดยเฉพาะ Discharge Valve ที่อาจถูกเปิดกว้างเกินไป[^6][^12]

แบบที่สองคือ Mechanical Binding ซึ่งอันตรายกว่า เมื่อมีวัตถุแปลกปลอมเข้าไปติดอยู่ใน Impeller หรือ Impeller ติดกับ Casing ปั๊มจะหยุดทันทีและมอเตอร์จะ Trip ทันทีเช่นกัน ในกรณีนี้ห้าม Restart โดยเด็ดขาดก่อนที่จะเปิด Casing ตรวจสอบและนำสิ่งแปลกปลอมออก เพราะถ้า Restart โดยที่ยังมีการติดขัดอยู่ มอเตอร์จะเสียหายหนักขึ้น[^4]
### Cavitation — เสียงปั๊มผิดปกติ
Cavitation เป็นปรากฏการณ์ที่ทำลาย Impeller ได้อย่างรวดเร็วและรุนแรงที่สุด เกิดขึ้นเมื่อแรงดันที่ Suction ต่ำจนน้ำเดือดกลายเป็นฟองภายในปั๊ม ฟองเหล่านี้จะยุบตัวอย่างรุนแรงเมื่อผ่านเข้าสู่บริเวณแรงดันสูง สร้างแรงกระแทกขนาดเล็กแต่ถี่มาก สัญญาณจาก Sensor ที่บ่งชี้ถึง Cavitation คือแรงดันต่ำร่วมกับ Flow Rate ที่ผันผวนไม่คงที่ เสียงที่ได้ยินจากภายนอกจะคล้ายกับเสียงกรวดถูกปั่น วิธีแก้คือเพิ่ม NPSH Available โดยการลด Suction Lift, เพิ่มระดับน้ำในถัง หรือขยาย Suction Pipe เพื่อลดความเร็วน้ำและเพิ่มแรงดัน[^4][^5]

***
## ฉบับที่ 3 — ขั้นตอนการบำรุงรักษา (Maintenance SOP)
การบำรุงรักษา Centrifugal Pump แบ่งออกเป็น 4 ระดับตามความถี่และความลึกของการตรวจสอบ แต่ละระดับมีผู้รับผิดชอบและเวลาที่ใช้ต่างกัน[^13][^11]
### การตรวจสอบรายวัน (Daily Inspection)
งานนี้ใช้เวลาประมาณ 10 ถึง 15 นาทีและเป็นหน้าที่ของ Operator ประจำสาย เริ่มจากการอ่านค่า Dashboard และ Sensor ทุกตัวเพื่อยืนยันว่าทุกค่าอยู่ใน Normal Zone ถ้าพบค่าใดอยู่ใน Warning Zone ให้บันทึกลง Log Sheet พร้อม Timestamp และแจ้ง Maintenance ทันที[^14]

จากนั้นให้เดินรอบปั๊มและฟังเสียงอย่างตั้งใจ เสียงดังผิดปกติหรือเสียงกรวดถูกปั่นคือสัญญาณของ Cavitation หรือ Bearing กำลังเสื่อมที่ต้องรายงานทันที ให้ตรวจ Seal บริเวณ Shaft ด้วยสายตาว่ามีน้ำหรือของเหลวรั่วออกมาหรือไม่ สำหรับ Mechanical Seal ไม่ควรมีการรั่วเลย แต่สำหรับ Packing Seal อนุญาตให้หยดประมาณ 1 ถึง 2 หยดต่อนาทีซึ่งเป็นสิ่งจำเป็นเพื่อ Lubrication[^10][^15]

สุดท้ายให้ตรวจระดับน้ำมันที่ Sight Glass ของ Bearing Housing ระดับต้องอยู่ระหว่างเส้น Min และ Max เสมอ ถ้าต่ำกว่า Min ให้เติมน้ำมัน ISO VG 46 ทันทีโดยไม่ต้องรอ[^11]
### การตรวจสอบรายสัปดาห์ (Weekly Inspection)
งานนี้ใช้เวลาประมาณ 30 ถึง 45 นาทีและทำโดย Maintenance Technician เริ่มจากการวัดแรงดันที่ Suction และ Discharge พร้อมกันเพื่อคำนวณ Differential Pressure แล้วเปรียบเทียบกับค่า Baseline ที่บันทึกไว้ตอน Commissioning ถ้า Differential Pressure ลดลงมากกว่า 10 เปอร์เซ็นต์อาจหมายถึง Impeller เริ่มสึกหรือ Wear Ring เริ่มกว้างเกิน[^10][^15]

ให้ตรวจ Anchor Bolt และ Shock Mount ทุกจุดว่ายังแน่นหนาดีหรือไม่ การสั่นสะเทือนระหว่างการทำงานจะค่อยๆ ทำให้ Bolt คลายตัวในระยะยาว จากนั้นวัดอุณหภูมิ Bearing Housing ด้วย Infrared Thermometer เปรียบเทียบกับค่าจาก Temperature Sensor ที่ติดตั้งอยู่ ถ้าค่าต่างกันเกิน 5 องศาเซลเซียส ให้ตรวจสอบ Sensor Calibration[^3][^10]

ปิดท้ายด้วยการตรวจ Coupling ว่า Flexible Element ยังอยู่ในสภาพดีไม่แตกหรือชำรุด Coupling ที่เสื่อมจะทำให้เกิด Vibration และตามมาด้วย Misalignment ได้[^11]
### การบำรุงรักษารายสามเดือน (Quarterly Maintenance)
งานนี้ใช้เวลา 2 ถึง 4 ชั่วโมงและต้องการ Senior Maintenance Technician งานหลักคือการเปลี่ยนน้ำมัน Bearing Housing ให้ทิ้งน้ำมันเก่าออกให้หมด ล้าง Housing ด้วย Flushing Oil แล้วเติมน้ำมัน ISO VG 46 ใหม่จนถึงระดับกึ่งกลาง Sight Glass น้ำมันที่ใช้งานมากกว่า 2,000 ชั่วโมงจะเปลี่ยนสีเป็นสีเข้มและมีตะกอน ถือว่าเสื่อมสภาพและต้องเปลี่ยน[^10][^11]

ให้ตรวจสอบและปรับ Shaft Alignment ด้วย Dial Indicator โดยวัดทั้ง Radial Runout ที่ไม่ควรเกิน 0.05 มิลลิเมตร และ Angular Misalignment ที่ไม่ควรเกิน 0.05 มิลลิเมตรต่อ 100 มิลลิเมตร ถ้าค่าเกินกำหนดให้ปรับ Shim ใต้ฐานปั๊มหรือมอเตอร์จนได้ค่าที่ถูกต้อง[^11]

ตรวจหน้าสัมผัส Mechanical Seal ด้วยสายตาหลังเปิด Cover ออก ถ้าพบรอยขีด การกัดกร่อน หรือ Erosion ที่ผิดสม่ำเสมอ ให้วางแผนเปลี่ยน Seal ในรอบถัดไปโดยไม่ต้องรอให้รั่วก่อน[^15]
### การถอดตรวจประจำปี (Annual Overhaul)
งานนี้ต้องหยุดเครื่องอย่างน้อย 1 ถึง 2 วัน และต้องมีทั้ง Senior Technician และ Engineer ร่วมดำเนินการ ขั้นตอนแรกก่อนแตะอุปกรณ์ใดๆ คือการทำ Lockout/Tagout (LOTO) อย่างสมบูรณ์ ตัด Power มอเตอร์ที่ MCC แขวน Lock และป้ายห้ามเปิดส่วนตัว เปิด Vent ระบาย Pressure ในระบบให้เป็นศูนย์ ระบาย Draining ของเหลวออก และยืนยันว่าแรงดันเป็นศูนย์ก่อนถอด Flange ใดๆ การข้ามขั้นตอนนี้อาจเป็นอันตรายถึงชีวิต[^13]

หลัง LOTO ให้ถอด Coupling, Bearing Housing ทั้งฝั่ง Drive End และ Non-Drive End บันทึกค่า Bearing Clearance ก่อนถอดเพื่อเปรียบเทียบกับค่าเดิมที่ Commissioning จากนั้นดึง Impeller ออกตรวจสอบ Blade ทุกใบว่ามีรอยสึก Erosion หรือ Crack ถ้าน้ำหนักของ Impeller ไม่สมมาตรจากการสึกหรอ ต้องนำไป Rebalance ก่อนประกอบกลับ[^10][^16][^17]

ชิ้นส่วนที่ต้องเปลี่ยนทุกปีโดยไม่ต้องรอให้เสีย ได้แก่ Mechanical Seal, O-Ring ทุกชุด, Gasket ทุกชุด และน้ำมัน Bearing Housing ส่วน Ball Bearing ให้เปลี่ยนเมื่อวัด Clearance แล้วเกินมาตรฐาน หลังประกอบกลับครบให้ทำ Shaft Alignment ใหม่ทั้งหมด แล้ว Start No-Load 30 นาทีเพื่อตรวจสอบ Leakage, Vibration, Temperature และ Pressure ก่อน Return to Service[^11][^10]

***
## ฉบับที่ 4 — รายการอะไหล่ (Spare Parts List)
การมีอะไหล่พร้อมเป็นความแตกต่างระหว่างการซ่อมภายในชั่วโมงกับการรอเป็นวัน เอกสารนี้แบ่งอะไหล่ออกเป็น 3 หมวดตามลักษณะการใช้งาน[^10][^16][^17]
### หมวด A — อะไหล่ที่เปลี่ยนตามกำหนดเวลา (Consumable Parts)
อะไหล่ในหมวดนี้ต้องเปลี่ยนตามรอบเวลาโดยไม่ต้องรอให้เสียก่อน เพราะต้นทุนของอะไหล่ถูกกว่าค่า Downtime มาก

Mechanical Seal เป็นอะไหล่ที่สำคัญที่สุดในหมวดนี้ ควรเปลี่ยนทุก 12 เดือนหรือทันทีที่พบการรั่ว ควรสต็อกไว้อย่างน้อย 2 ชุดพร้อมใช้เสมอ พร้อมกับ O-Ring Set และ Gasket Set ที่ต้องเปลี่ยนพร้อมกับ Seal ทุกครั้งที่ Overhaul เพราะ O-Ring และ Gasket เก่าจะไม่ซีลได้ดีเท่า Seal ใหม่[^10][^15]

น้ำมัน Bearing Housing ISO VG 46 ต้องสต็อกไว้สำหรับการเติมรายสัปดาห์และการเปลี่ยนทุก 3 เดือน ควรมีอย่างน้อย 5 กระป๋องเสมอ Suction Strainer Screen ต้องเปลี่ยนทุก 6 เดือนหรือเมื่ออุดตัน ควรสต็อกไว้ 2 ชิ้น[^10]
### หมวด B — อะไหล่ที่เปลี่ยนตามสภาพ (Wear Parts)
อะไหล่ในหมวดนี้ต้องวัดและตรวจสอบก่อนตัดสินใจเปลี่ยน ไม่ได้เปลี่ยนตามรอบเวลาตายตัว[^10][^16]

Impeller เป็นหัวใจของปั๊ม ให้เปลี่ยนเมื่อ Blade สึกเกิน 10 เปอร์เซ็นต์ของหน้าตัด หรือพบรอย Crack ใดๆ ควรสต็อกไว้ 1 ชิ้นเสมอเพราะมักมี Lead Time นาน Wear Ring ให้เปลี่ยนเมื่อ Clearance เกิน 0.8 มิลลิเมตร ซึ่งจะส่งผลให้ Flow Rate ลดลงอย่างเห็นได้ชัด[^5][^15]

Ball Bearing ทั้งฝั่ง Drive End และ Non-Drive End ให้เปลี่ยนเมื่อ Clearance เกินมาตรฐานหรือเมื่ออุณหภูมิ Trending สูงขึ้นเรื่อยๆ แม้จะไม่ถึงค่า Critical ควรสต็อก Bearing แต่ละตำแหน่งไว้อย่างน้อย 2 ชิ้น Shaft Sleeve ให้เปลี่ยนเมื่อพบรอยสึกลึกเกิน 0.5 มิลลิเมตรหรือมี Groove จาก Mechanical Seal กัดกร่อน และ Coupling Flexible Element ให้เปลี่ยนทันทีที่พบรอยแตกร้าวหรือการ Deform ใดๆ เพราะ Coupling เสื่อมจะทำให้เกิด Vibration ที่ทำลาย Bearing และ Seal ตามมา[^11][^18]
### หมวด C — อะไหล่สำรองฉุกเฉิน (Emergency Parts)
อะไหล่ในหมวดนี้ไม่ได้เปลี่ยนตามกำหนด แต่เมื่อเสียจะทำให้ปั๊มหยุดทันทีและต้องการการซ่อมด่วน การมีสต็อกไว้คือการลงทุนในความพร้อมของสายการผลิต[^10]

Mechanical Seal Emergency ควรสต็อกแยกต่างหากจาก Consumable Seal เพื่อให้แน่ใจว่าเมื่อเกิดเหตุฉุกเฉินยังมีชิ้นส่วนใช้ได้ทันที Shaft Complete ควรมี 1 ชิ้นสำรอง เพราะ Shaft ที่บิดหรือหัก จะทำให้ปั๊มต้องหยุดยาวและมี Lead Time สั่งซื้อนานมาก Bearing Set ครบชุด (ทั้ง Drive End และ Non-Drive End) ควรมีไว้ 1 ชุดในสต็อก Emergency เพราะ Bearing Failure กะทันหันทำให้ Shaft ล็อกและไม่สามารถ Restart ได้เลย และ Impeller Emergency ควรมี 1 ชิ้นสำรองสำหรับกรณีที่ Foreign Object เข้าไปทำให้ Impeller แตก[^18]

เมื่อ AI Agent วินิจฉัย Fault ใดๆ ได้แล้ว ให้ตรวจสอบกับสต็อกทันทีตามการ Map นี้ ถ้าวินิจฉัยว่า Seal รั่ว ให้เตรียม Mechanical Seal, O-Ring Set, Gasket Set และ Shaft Sleeve ถ้าวินิจฉัยว่า Cavitation หรือ Flow ต่ำเรื้อรัง ให้เตรียม Impeller, Wear Ring และ Suction Strainer ถ้าวินิจฉัยว่า Bearing Overheating ให้เตรียม Ball Bearing ทั้งสองฝั่ง, น้ำมันใหม่ และ Coupling Flexible Element และถ้าวินิจฉัยว่า Vibration ผิดปกติ ให้เตรียม Bearing Set และ Coupling พร้อมกับตรวจสอบ Impeller Balance ด้วย

อะไหล่ในหมวด Consumable มักมีใน Stock ของ Distributor ในประเทศ สั่งได้ภายใน 1 ถึง 3 วัน ส่วนหมวด Wear Parts อาจใช้เวลา 3 ถึง 14 วัน และหมวด Emergency ควรประสาน Vendor ล่วงหน้าเพื่อยืนยัน Lead Time และควรสั่งเพิ่มทันทีที่หยิบชิ้นส่วนจาก Emergency Stock ออกมาใช้[^10]

***

*เอกสารชุดนี้จัดทำสำหรับใช้เป็น Knowledge Base ใน RAG System ของ AI Prescriptive Maintenance Agent เวอร์ชัน 1.0 อ้างอิงจากมาตรฐาน JB/T5294-91, GB3215-82, SOP อุตสาหกรรม และคู่มือ Centrifugal Pump จาก Hydraulic Institute*[^13][^11][^1][^3][^19]

---

## References

1. [Split Case Pump (other Centrifugal Pumps) Bearing ...](https://www.chinacredopump.com/Technology-service/split-case-pump-other-centrifugal-pumps-bearing-temperature-standard) - Maintaining the correct bearing temperature is essential to ensuring the efficient operation and lon...

2. [Technology Service](https://en.credopump.com/hr/Technology-service/split-case-pump-other-centrifugal-pumps-bearing-temperature-standard) - Considering the ambient temperature of 40°C, the maximum operating temperature of the motor cannot e...

3. [Bearing Temperature Standards and Maintenance ...](https://chinacredopump.com/bearing-temperature-guidelines-for-axial-split-case-pumps/) - This article provides a comprehensive overview of bearing temperature standards for axial split case...

4. [Troubleshooting Centrifugal Pumps: Common Problems ...](https://www.pumpworks.com/troubleshooting-centrifugal-pumps-common-problems/) - We created this troubleshooting guide for your centrifugal pump, exploring the typical problems that...

5. [Fault Finding Centrifugal Pump | Step by Step Guide](https://esitechgroup.com/knowledge-centre/fault-finding-centrifugal-pump/) - If the centrifugal pump is not primed – re-prime the pump and check that the pump and suction line i...

6. [Centrifugal Pump Datasheet - Key Parameters Reference](https://autotbe.aza55.com/pump/centrifugal-pump/datasheet-key-parameters) - Complete guide to centrifugal pump datasheet parameters. Covers process data, mechanical specificati...

7. [Centrifugal Pump RPM to Flow Rate Linear Relationship Guide](https://industrialmonitordirect.com/blogs/knowledgebase/centrifugal-pump-rpm-to-flow-rate-linear-relationship-guide) - Your experiment showing 1000 RPM = 90 mL/min vs manufacturer's 100 mL/min is normal. The linear tren...

8. [Understanding Centrifugal Pump Flow Rate: Formula and Calculation](https://www.rotechpumps.com/centrifugal-pump-flow-rate/) - Understanding the Basic Formula: The flow rate (Q) of a centrifugal pump can be calculated using the...

9. [Centrifugal Pump Minute-Troubleshooting: Bearings Run Hot](https://empoweringpumps.com/psg-centrifugal-pump-minute-troubleshooting-bearings-run-hot/) - In the latest edition of the Centrifugal Pump Minute, James Farley, of Product Management for Griswo...

10. [Centrifugal Pump Maintenance Schedule](https://www.castlepumps.com/info-hub/centrifugal-pump-maintenance-schedule) - Centrifugal pumps are one of the most popular pumping solutions in the world but, just like any othe...

11. [STANDARD OPERATING PROCEDURE](https://pharmadevils.com/wp-content/uploads/2024/07/SOP-for-Preventive-Maintenance-of-Centrifugal-Pumps.pdf)

12. [Centrifugal Pump Troubleshooting: Excessive Power Required](https://www.youtube.com/watch?v=bI-GIeqU6js) - Why is your centrifugal pump operating with excessive power? In this edition of the Centrifugal Pump...

13. [SOP for Maintenance of Horizontal Overhung Centrifugal ...](https://www.studocu.com/fr-ca/document/college-lionel-groulx/ecriture-et-litterature/pump-maintenance/66485025) - Form No. : EHSMSM/446/4013 Form Rev. No. : 01 Effective date: SOP No.

14. [Centrifugal Pump Maintenance Checklist for Peak Performance](https://www.rotechpumps.com/centrifugal-pump-maintenance-checklist/) - Optimize your centrifugal pump's performance with our comprehensive maintenance checklist. Ensure ef...

15. [Downloadable Centrifugal Pump Maintenance Checklist ...](https://www.zapium.com/checklist/centrifugal-pump-maintenance/) - Get the free, downloadable centrifugal pump maintenance checklist template for regular inspections a...

16. [Centrifugal Pump Parts](https://hardhatengineer.com/centrifugal-pump-parts/) - Learn about 9 centrifugal pump parts such as Casing, Impeller, wear Ring, Shaft, coupling, Bearing a...

17. [Top 15 Centrifugal Pump Components You Should Know About](https://www.crompton.co.in/blogs/pumps-guide/centrifugal-pump-components) - Here is a list of components of centrifugal pumps: Impeller; Volute Casing; Shaft; Bearings; Seals; ...

18. [[PDF] Bearings in centrifugal pumps | SKF](https://www.skf.com/binaries/pub12/Images/0901d19680054a8a-100-955-Bearings-in-centrifugal-pumps_tcm_12-154513.pdf) - Pump bearings keep the shaft axial end movement and lateral deflection within acceptable limits for ...

19. [Hydraulic Institute Pump FAQs August 2008](https://www.pumpsandsystems.com/hydraulic-institute-pump-faqs-august-2008) - Q. What is the maximum pumped liquid temperature that an end suction centrifugal pump can handle, an...

21

