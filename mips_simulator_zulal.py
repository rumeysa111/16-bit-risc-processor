import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
import ttkthemes

# 8 Register tanımı ve başlangıç değerleri
register_names = [f"R{i}" for i in range(8)]  # R0 - R7
registers = {name: 0 for name in register_names}
memory = [0] * 512  # 512 byte'lık bellek
instruction_memory = [""] * 512  # 512 byte'lık Instruction Memory
labels = {}  # Label'ların satır numaralarını tutar
pc = 0  # Program Counter
realistic_pc = 0  # Donanımsal PC
commands = []  # Komut listesi
pipeline_stages = {"IF": "Empty", "ID": "Empty", "EX": "Empty", "MEM": "Empty", "WB": "Empty"}
hazards = []




# Komutları yükleyen fonksiyon
def load_commands():
    global commands, labels, pc, realistic_pc
    commands = input_text.get("1.0", tk.END).strip().split("\n")
    labels = {}
    pc = 0
    realistic_pc = 0
    cleaned_commands = []

    # Instruction memory'yi temizle
    instruction_memory.clear()
    instruction_memory.extend([""] * 512)

    for i, command in enumerate(commands):
        command = command.strip()
        if ":" in command:  # Etiket var mı kontrol et
            parts = command.split(":")
            label = parts[0].strip()
            labels[label] = len(cleaned_commands)  # Etiketi geçerli komut satırına bağla
            if len(parts) > 1 and parts[1].strip():
                cleaned_commands.append(parts[1].strip())
        else:
            cleaned_commands.append(command)

    commands = cleaned_commands
    for i, command in enumerate(commands):
        if i < len(instruction_memory):
            instruction_memory[i] = command
        else:
            break

    # Pipeline'ı başlangıç durumuna getir
    if len(commands) > 0:
        pipeline_stages["IF"] = "Empty"  # İlk aşama boş başlasın
        pipeline_stages["ID"] = "Empty"
        pipeline_stages["EX"] = "Empty"
        pipeline_stages["MEM"] = "Empty"
        pipeline_stages["WB"] = "Empty"

    
    result_label.configure(text="Komutlar yüklendi!", foreground="blue")
    update_instruction_memory_display()
    update_pipeline_stages()

def process_labels():
    global labels
    for i, command in enumerate(commands):
        command = command.strip()
        if command and command[-1] == ":":  # Etiket satırı
            label = command[:-1]  # ":" işaretini kaldır
            labels[label] = i  # Etiketi labels sözlüğüne ekle 

# Tek bir komutu işleyen fonksiyon
def step_command():
    global pc, realistic_pc
    instruction = fetch_instruction(pc)  # Instruction Memory'den komut al
    if instruction is None or instruction.strip() == "":
        result_label.configure(text="Program sonlandı.", foreground="green")
        return

    parts = instruction.strip().split()  # Komut parçalarını ayır

    
    try:
        if parts[0] == "add":  # R-Type add
            rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            registers[rd] = registers[rs] + registers[rt]
        elif parts[0] == "sub":  # R-Type sub
            rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            registers[rd] = registers[rs] - registers[rt]
        elif parts[0] == "and":  # R-Type and
            rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            registers[rd] = registers[rs] & registers[rt]
        elif parts[0] == "or":  # R-Type or
            rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            registers[rd] = registers[rs] | registers[rt]
        elif parts[0] == "slt":  # R-Type slt
            rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            registers[rd] = 1 if registers[rs] < registers[rt] else 0
        elif parts[0] == "sll":  # R-Type sll
            rd, rt, shamt = parts[1].rstrip(","), parts[2].rstrip(","), int(parts[3])
            registers[rd] = registers[rt] << shamt
        elif parts[0] == "srl":  # R-Type srl
            rd, rt, shamt = parts[1].rstrip(","), parts[2].rstrip(","), int(parts[3])
            registers[rd] = registers[rt] >> shamt
        elif parts[0] == "addi":  # I-Type addi
            if len(parts) != 4:
                result_label.configure(text=f"Geçersiz addi komutu: {instruction}", foreground="red")
                return
            try:
                rt, rs, imm = parts[1].rstrip(","), parts[2].rstrip(","), int(parts[3])
                if rt not in registers or rs not in registers:
                    result_label.configure(text=f"Geçersiz register: {rt} veya {rs}", foreground="red")
                    return
                registers[rt] = registers[rs] + imm
            except ValueError:
                result_label.configure(text=f"Geçersiz immediate değer: {parts[3]}", foreground="red")
                return
        elif parts[0] == "sw":  # I-Type sw
            rt, offset_rs = parts[1].rstrip(","), parts[2]
            offset, rs = offset_rs.split("(")
            rs = rs.rstrip(")")
            address = registers[rs] + int(offset)
            if 0 <= address < len(memory):  # Bellek sınırı kontrolü
                memory[address] = registers[rt]
                update_memory_display()  # Belleği güncelle
            else:
                result_label.configure(text=f"Geçersiz bellek adresi: {address}", foreground="red")
                return

        elif parts[0] == "lw":  # I-Type lw
            rt, offset_rs = parts[1].rstrip(","), parts[2]
            offset, rs = offset_rs.split("(")
            rs = rs.rstrip(")")
            address = registers[rs] + int(offset)
            if 0 <= address < len(memory):  # Bellek sınırı kontrolü
                registers[rt] = memory[address]
            else:
                result_label.configure(text=f"Geçersiz bellek adresi: {address}", foreground="red")
                return

        elif parts[0] == "beq":  # I-Type beq
            rs, rt, label = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            if registers[rs] == registers[rt]:
                if label in labels:
                    pc = labels[label]  # Etiketle yönlendir
                    realistic_pc = pc * 2  # Realistic PC'yi güncelle
                    update_pc_display()
                    update_instruction_memory_display()  # Dinamik olarak Instruction Memory'yi güncelle
                    update_register_display()

                    return
                else:
                    result_label.configure(text=f"Etiket bulunamadı: {label}", foreground="red")
                    return
            else:
                pc+=1
                realistic_pc+=2
                update_pc_display()
                return

        elif parts[0] == "bne":  # I-Type bne
            rs, rt, label = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            if registers[rs] != registers[rt]:
                if label in labels:
                    pc = labels[label]  # Etiketle yönlendir
                    realistic_pc = pc * 2  # Realistic PC'yi güncelle
                    update_pc_display()
                    update_instruction_memory_display()  # Instruction Memory'yi güncelle
                    update_register_display()
                   
                    return
                else:
                    result_label.configure(text=f"Etiket bulunamadı: {label}", foreground="red")
                    return
            pc+=1
            realistic_pc +=1
            update_memory_display()

        elif parts[0] == "j":  # J-Type j
            label = parts[1]
            if label in labels:
                pc = labels[label]
                realistic_pc = pc * 2  # Realistic PC'yi güncelle
                update_pc_display()
                update_register_display()
           
                return
            else:
                result_label.configure(text=f"Etiket bulunamadı: {label}", foreground="red")
                return

        elif parts[0] == "jal":  # J-Type jal
            label = parts[1]
            if label in labels:
                registers["$ra"] = pc + 1  # Return Address
                pc = labels[label]
                realistic_pc = pc * 2  # Realistic PC'yi güncelle
                update_pc_display()
                update_register_display()
              
                return
            else:
                result_label.configure(text=f"Etiket bulunamadı: {label}", foreground="red")
                return

        elif parts[0] == "jr":  # J-Type jr
            rs = parts[1]
            pc = registers[rs]
            realistic_pc = pc * 2  # Realistic PC'yi güncelle
            update_pc_display()
            update_instruction_memory_display()
            update_register_display()
 
            result_label.configure(text=f"Komut işlendi: jr {rs} (Realistic PC: {realistic_pc})", foreground="blue")  # Doğru değeri yazdır
            return

        else:
            result_label.configure(text=f"Geçersiz komut: {instruction}", foreground="red")
            return
    except KeyError:
        result_label.configure(text=f"Register hatası: {instruction}", foreground="red")
        return
    except ValueError:
        result_label.configure(text=f"Geçersiz değer: {instruction}", foreground="red")
        return

    pc += 1  # Bir sonraki komuta geç
    realistic_pc +=2
    update_pc_display()
    update_register_display()
   
    result_label.configure(text=f"Komut işlendi: {instruction}", foreground="blue")

def run_command():
    global pc, realistic_pc
    while pc < len(instruction_memory):  # Program Counter, komut belleğinin sınırları içinde
        instruction = fetch_instruction(pc)  # Komutu al
        if instruction is None or instruction.strip() == "":  # Eğer komut yoksa programı sonlandır
            break

        parts = instruction.strip().split()  # Komut parçalarına ayır
        if not parts:  # Eğer boş bir komutsa bir sonraki komuta geç
            pc += 1
            realistic_pc+=2
            update_pc_display()
            continue

        try:
            if parts[0] == "add":  # R-Type add
                rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
                registers[rd] = registers[rs] + registers[rt]
            elif parts[0] == "sub":  # R-Type sub
                rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
                registers[rd] = registers[rs] - registers[rt]

            elif parts[0] == "and":  # R-Type and
                    rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
                    registers[rd] = registers[rs] & registers[rt]
            elif parts[0] == "or":  # R-Type or
                    rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
                    registers[rd] = registers[rs] | registers[rt]
            elif parts[0] == "slt":  # R-Type slt
                    rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
                    registers[rd] = 1 if registers[rs] < registers[rt] else 0
            elif parts[0] == "sll":  # R-Type sll
                    rd, rt, shamt = parts[1].rstrip(","), parts[2].rstrip(","), int(parts[3])
                    registers[rd] = registers[rt] << shamt
            elif parts[0] == "srl":  # R-Type srl
                    rd, rt, shamt = parts[1].rstrip(","), parts[2].rstrip(","), int(parts[3])
                    registers[rd] = registers[rt] >> shamt

            elif parts[0] == "addi":  # I-Type addi
                rt, rs, imm = parts[1].rstrip(","), parts[2].rstrip(","), int(parts[3])
                if rt in registers and rs in registers:
                    registers[rt] = registers[rs] + imm
                else:
                    result_label.configure(text=f"Geçersiz register: {rt} veya {rs}", foreground="red")
                    return
                
            elif parts[0] == "sw":  # I-Type sw
                    rt, offset_rs = parts[1].rstrip(","), parts[2]
                    offset, rs = offset_rs.split("(")
                    rs = rs.rstrip(")")
                    address = registers[rs] + int(offset)
                    if 0 <= address < len(memory):  # Bellek sınırı kontrolü
                        memory[address] = registers[rt]
                        update_memory_display()  # Belleği güncelle
                    else:
                        result_label.configure(text=f"Geçersiz bellek adresi: {address}", foreground="red")
                        return

            elif parts[0] == "lw":  # I-Type lw
                    rt, offset_rs = parts[1].rstrip(","), parts[2]
                    offset, rs = offset_rs.split("(")
                    rs = rs.rstrip(")")
                    address = registers[rs] + int(offset)
                    if 0 <= address < len(memory):  # Bellek sınırı kontrolü
                        registers[rt] = memory[address]
                    else:
                        result_label.configure(text=f"Geçersiz bellek adresi: {address}", foreground="red")
                        return

            elif parts[0] == "beq":  # I-Type beq
                rs, rt, label = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
                if rs in registers and rt in registers:
                    if registers[rs] == registers[rt]:  # Dallanma
                        if label in labels:
                            pc = labels[label]
                            realistic_pc = pc * 2
                            update_instruction_memory_display()  # Dallanma sonrası komutları göster
                            continue
                        else:
                            result_label.configure(text=f"Etiket bulunamadı: {label}", foreground="red")
                            return
            elif parts[0] == "bne":  # I-Type bne
                rs, rt, label = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
                if rs in registers and rt in registers:
                    if registers[rs] != registers[rt]:  # Dallanma
                        if label in labels:
                            pc = labels[label]
                            realistic_pc = pc * 2
                            update_instruction_memory_display()  # Dallanma sonrası komutları göster
                            continue
                        else:
                            result_label.configure(text=f"Etiket bulunamadı: {label}", foreground="red")
                            return
                        
            elif parts[0] == "j":  # J-Type j
                label = parts[1]
                if label in labels:
                    pc = labels[label]
                    realistic_pc = pc * 2
                    update_register_display()
                 
                    return
                else:
                    result_label.configure(text=f"Etiket bulunamadı: {label}", foreground="red")
                    return

            elif parts[0] == "jal":  # J-Type jal
                    label = parts[1]
                    if label in labels:
                        registers["$ra"] = pc + 1  # Return Address
                        pc = labels[label]
                        realistic_pc = pc * 2
                        update_register_display()                        
                     
                        return
                    else:
                        result_label.configure(text=f"Etiket bulunamadı: {label}", foreground="red")
                        return

            elif parts[0] == "jr":  # J-Type jr
                    rs = parts[1]
                    pc = registers[rs]
                    realistic_pc = pc * 2
                    update_instruction_memory_display()
                    update_register_display()
             
                    return    
                
            elif parts[0] == "halt":  # Halt komutu
                result_label.configure(text="Program sonlandı.", foreground="green")
                break
            else:
                result_label.configure(text=f"Geçersiz komut: {instruction}", foreground="red")
                return
        except KeyError:
            result_label.configure(text=f"Register hatası: {instruction}", foreground="red")
            return
        except ValueError:
            result_label.configure(text=f"Geçersiz değer: {instruction}", foreground="red")
            return

        pc += 1  # Bir sonraki komuta geç
        realistic_pc +=2
        update_pc_display()

    # İşlem tamamlandıktan sonra tüm ekranları güncelle
    update_register_display()  # Register'ları güncelle
    update_memory_display()  # Belleği güncelle
    update_machine_code_display()
    result_label.configure(text="Program sonlandı.", foreground="green")
# Register ekranını güncelleyen fonksiyon
def update_register_display():
    for i, name in enumerate(register_names):
        register_labels[i].configure(text=f"{name}: {registers[name]}")

# Register ekranını güncelleyen fonksiyon
def update_memory_display():
    memory_text.delete("1.0", tk.END)
    for i in range(0, len(memory), 4):  # 4 byte'lık bloklar halinde göster
        values = " ".join(f"{val:03}" for val in memory[i:i+4])
        memory_text.insert(tk.END, f"{i:03}: {values}\n")

def load_instruction_memory():
    global instruction_memory
    commands = input_text.get("1.0", tk.END).strip().split("\n")
    for i, command in enumerate(commands):
        if i < len(instruction_memory):
            instruction_memory[i] = command.strip()
        else:
            result_label.configure(text="Instruction Memory kapasitesini aştınız!", foreground="red")
            return
    result_label.configure(text="Instruction Memory yüklendi!", foreground="blue")
    update_instruction_memory_display()

def fetch_instruction(pc):
    if 0 <= pc < len(instruction_memory):
        instruction = instruction_memory[pc].strip()
        if instruction:  # Eğer komut boş değilse
            return instruction
        else:
            return None  # Boş komut durumunda None döner
    else:
        result_label.configure(text="Instruction Memory sınırını aştınız!", foreground="red")
        return None


def update_pc_display():
    realistic_pc_value_label.configure(text=f"Realistic PC: {realistic_pc:03}")

def update_instruction_memory_display():
    instruction_memory_text.delete("1.0", tk.END)
    instruction_memory_text.tag_config("executed", foreground="black")  # Çalıştırılan talimatlar siyah
    instruction_memory_text.tag_config("skipped", foreground="white")   # Atlanan talimatlar beyaz

    executed_instructions = set()  # Çalıştırılmış talimatların adreslerini tutmak için bir küme
    skipped_indices = set()  # Atlanan talimatların adreslerini tutmak için bir küme

    # Pipeline'daki talimatları belirle
    for stage in pipeline_stages.values():
        if stage != "Empty":
            try:
                instruction_index = instruction_memory.index(stage.strip())
                executed_instructions.add(instruction_index)
            except ValueError:
                continue

    # Atlanan talimatları belirlemek için dallanma kontrolü
    pc_values = [pc]  # Mevcut dallanma sonrası PC değerlerini kaydedin
    for i, instruction in enumerate(instruction_memory):
        if instruction.strip() and (instruction.startswith("beq") or instruction.startswith("bne") or instruction.startswith("j")):
            parts = instruction.split()
            label = parts[-1]  # Etiketin adı
            if label in labels:
                target_index = labels[label]
                if target_index > i:  # İleriye doğru bir dallanma varsa
                    skipped_indices.update(range(i + 1, target_index))
                    pc_values.append(target_index)

    # Talimatları ekle ve renklendir
    for i, instruction in enumerate(instruction_memory):
        if instruction.strip():  # Boş olmayan talimatları işler
            start = f"{i + 1}.0"
            end = f"{i + 1}.end"
            instruction_memory_text.insert(tk.END, f"{i:03}: {instruction}\n")

            if i in executed_instructions or i in pc_values:
                instruction_memory_text.tag_add("executed", start, end)  # Çalıştırılan talimat
            elif i in skipped_indices:
                instruction_memory_text.tag_add("skipped", start, end)  # Atlanan talimat


def load_all():
    global labels, instruction_memory, pc
    # Komutları çok satırlı girişten alın
    instructions = input_text.get("1.0", tk.END).strip().split("\n")  # Input alanından komutlar
    labels = {}  # Etiketleri sıfırla
    pc = 0  # Program Counter'ı sıfırla
    realistic_pc = 0
    instruction_memory = [""] * 512  # Instruction Memory'yi sıfırla

    # Komutları Instruction Memory'ye yükle
    for i, instruction in enumerate(instructions):
        instruction = instruction.strip()
        if i < len(instruction_memory):
            if ":" in instruction:  # Eğer bir etiket varsa
                parts = instruction.split(":")
                label = parts[0].strip()  # Etiket ismini al
                labels[label] = i  # Etiketin bulunduğu satırı kaydet
                if len(parts) > 1 and parts[1].strip():  # Etiket sonrası komut varsa
                    instruction_memory[i] = parts[1].strip()  # Komut kısmını yükle
                else:
                    instruction_memory[i] = ""  # Sadece etiket varsa komut boş
            else:
                instruction_memory[i] = instruction  # Komutu doğrudan yükle
        else:
            result_label.configure(text="Instruction Memory kapasitesini aştınız!", foreground="red")
            return

    # Yükleme işlemi tamamlandı
    result_label.configure(text="Komutlar ve Instruction Memory yüklendi!", foreground="blue")
    update_instruction_memory_display()
    update_machine_code_display()


    # Komutları Instruction Memory'ye ve gerekli yapıya yükle
    for i, command in enumerate(commands):
        if i < len(instruction_memory):
            instruction_memory[i] = command
        else:
            break

    if instruction_memory[0].strip() == "":
        result_label.configure(text="İlk talimat boş, lütfen kontrol edin.", foreground="red")
        return


        # Etiketleri ayıkla ve komutları işle
        if ":" in command:  # Label kontrolü
            parts = command.split(":")
            label = parts[0].strip()
            labels[label] = i  # Etiketin bulunduğu satırı kaydet
            if len(parts) > 1 and parts[1].strip():  # Etiket sonrası komut varsa
                commands[i] = parts[1].strip()
            else:
                commands[i] = ""  # Etiketi temizle
        else:
            commands[i] = command

    result_label.configure(text="Komutlar ve Instruction Memory yüklendi!", foreground="blue")
    update_instruction_memory_display()



# Pipeline adımlarını tanımlama
def get_pipeline_stages(instruction):
    opcode = instruction.split()[0]
    if opcode in ["add", "sub", "and", "or", "slt"]:
        return ["IF", "ID", "EX", "WB"]
    elif opcode in ["sll", "srl"]:
        return ["IF", "ID", "EX", "WB"]
    elif opcode == "addi":
        return ["IF", "ID", "EX", "WB"]
    elif opcode == "lw":
        return ["IF", "ID", "EX", "MEM", "WB"]
    elif opcode == "sw":
        return ["IF", "ID", "EX", "MEM"]
    elif opcode in ["beq", "bne"]:
        return ["IF", "ID", "EX"]
    elif opcode == "j":
        return ["IF", "ID"]
    elif opcode == "jal":
        return ["IF", "ID", "WB"]
    elif opcode == "jr":
        return ["IF", "ID"]
    else:
        return []


def clear_pipeline():
    """Pipeline'ı temizlemek için tüm aşamaları 'Empty' yapar."""
    global pipeline_stages
    pipeline_stages = {"IF": "Empty", "ID": "Empty", "EX": "Empty", "MEM": "Empty", "WB": "Empty"}
    update_pipeline_stages()


# Talimatları çalıştıran fonksiyon
def execute_instruction(instruction, write_back=False):
    global pc
    parts = instruction.split()
    opcode = parts[0]

    try:
        if opcode == "add":
            rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            registers[rd] = registers[rs] + registers[rt]
        elif opcode == "sub":
            rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            registers[rd] = registers[rs] - registers[rt]
        elif opcode == "and":
            rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            registers[rd] = registers[rs] & registers[rt]
        elif opcode == "or":
            rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            registers[rd] = registers[rs] | registers[rt]
        elif opcode == "addi":
            rt, rs, imm = parts[1].rstrip(","), parts[2].rstrip(","), int(parts[3])
            registers[rt] = registers[rs] + imm
        elif opcode == "lw":
            rt, offset_rs = parts[1].rstrip(","), parts[2]
            offset, rs = offset_rs.split("(")
            rs = rs.rstrip(")")
            address = registers[rs] + int(offset)
            registers[rt] = memory[address]
        elif opcode == "sw":
            rt, offset_rs = parts[1].rstrip(","), parts[2]
            offset, rs = offset_rs.split("(")
            rs = rs.rstrip(")")
            address = registers[rs] + int(offset)
            memory[address] = registers[rt]


        elif opcode == "beq":  # I-Type beq
            rs, rt, label = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            if registers[rs] == registers[rt]:
                if label in labels:
                    pc = labels[label]  # Etiketle yönlendir
                    clear_pipeline()  # Pipeline'ı temizle
                    return
                else:
                    result_label.configure(text=f"Etiket bulunamadı: {label}", foreground="red")
                    return



                
        elif opcode == "bne":  # I-Type bne
            rs, rt, label = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            if registers[rs] != registers[rt]:
                if label in labels:
                    pc = labels[label]  # Etiketle yönlendir
                    clear_pipeline()  # Pipeline'ı temizle
                    return
                else:
                    result_label.configure(text=f"Etiket bulunamadı: {label}", foreground="red")
                    return





        elif opcode == "j":
            label = parts[1]
            pc = labels[label]
        elif opcode == "jal":
            label = parts[1]
            registers["R7"] = pc  # Return address
            pc = labels[label]
        elif opcode == "jr":
            rs = parts[1]
            pc = registers[rs]

        # Güncelleme işlemleri
        update_register_display()
        update_memory_display()
        update_pc_display()

    except KeyError as e:
        result_label.configure(text=f"Hata: Yanlış register ismi ({e})", foreground="red")
    except IndexError:
        result_label.configure(text="Hata: Eksik parametre", foreground="red")
    except ValueError:
        result_label.configure(text="Hata: Geçersiz sayı formatı", foreground="red")


# Pipeline aşamalarını güncelleyen fonksiyon
def update_pipeline_stages():
    pipeline_text.delete("1.0", tk.END)
    for stage, instruction in pipeline_stages.items():
        pipeline_text.insert(tk.END, f"{stage}: {instruction or 'Empty'}\n")


def detect_hazards():
    hazards.clear()
    
    # Data Hazard Kontrolü
    # EX ve MEM aşamalarındaki veri bağımlılığı kontrolü
    if pipeline_stages["EX"] and pipeline_stages["MEM"]:
        ex_parts = pipeline_stages["EX"].split()
        mem_parts = pipeline_stages["MEM"].split()
        if len(ex_parts) > 1 and len(mem_parts) > 1:
            # EX aşamasındaki bir register, MEM aşamasında hala yazılıyor olabilir
            if ex_parts[1] in mem_parts[1:]:
                hazards.append(f"Data hazard detected between EX and MEM: {ex_parts[1]}")

    # MEM ve WB aşamalarındaki veri bağımlılığı kontrolü
    if pipeline_stages["MEM"] and pipeline_stages["WB"]:
        mem_parts = pipeline_stages["MEM"].split()
        wb_parts = pipeline_stages["WB"].split()
        if len(mem_parts) > 1 and len(wb_parts) > 1:
            # MEM aşamasındaki bir register, WB aşamasında hala yazılıyor olabilir
            if mem_parts[1] in wb_parts[1:]:
                hazards.append(f"Data hazard detected between MEM and WB: {mem_parts[1]}")

    # Control Hazard Kontrolü
    # IF ve ID aşamalarındaki branching kontrolü
    if pipeline_stages["IF"] and pipeline_stages["ID"]:
        if any(pipeline_stages["IF"].startswith(branch) for branch in ["beq", "bne", "j", "jal"]):
            # Branch talimatı IF aşamasındayken ID aşamasında diğer komut çalıştırılabilir
            hazards.append(f"Control hazard detected in IF stage due to branching.")

    # Hazard ekranını güncelle
    update_hazard_display()


def update_hazard_display():
    hazard_text.delete("1.0", tk.END)
    if hazards:
        for hazard in hazards:
            hazard_text.insert(tk.END, f"{hazard}\n")
    else:
        hazard_text.insert(tk.END, "No hazards detected.\n")

# Tek bir komutu işleyen ve pipeline'a entegre eden fonksiyon
def step_pipeline():
    global pc, realistic_pc, hazards

    # WB aşamasındaki talimatı çalıştır
    if pipeline_stages["WB"] != "Empty":
        execute_instruction(pipeline_stages["WB"], write_back=True)
        pipeline_stages["WB"] = "Empty"  # WB aşamasını boşalt

    # Pipeline aşamalarını kaydır
    pipeline_stages["WB"] = pipeline_stages["MEM"]
    pipeline_stages["MEM"] = pipeline_stages["EX"]
    pipeline_stages["EX"] = pipeline_stages["ID"]
    pipeline_stages["ID"] = pipeline_stages["IF"]

    # Yeni talimatı IF aşamasına yükle
    if pc < len(instruction_memory) and instruction_memory[pc].strip():
        pipeline_stages["IF"] = instruction_memory[pc]
        pc += 1
        realistic_pc += 2
    else:
        pipeline_stages["IF"] = "Empty"

    # Hazardları kontrol et ve güncelle
    detect_hazards()
    update_pipeline_stages()
    update_register_display()
    update_memory_display()
    update_pc_display()


# Bellek görüntülemesi
def update_memory_display():
    memory_text.delete("1.0", tk.END)
    for i in range(0, len(memory), 4):  # 4 byte'lık bloklar halinde göster
        values = " ".join(f"{val:03}" for val in memory[i:i+4])
        memory_text.insert(tk.END, f"{i:03}: {values}\n")

# Pipeline ve Register Arasındaki GUI Sentezi
def update_pc_display():
    realistic_pc_value_label.configure(text=f"Realistic PC: {realistic_pc:03}")

def update_register_display():
    for i, name in enumerate(register_names):
        register_labels[i].configure(text=f"{name}: {registers[name]}")

# Instruction Memory ekranını güncelleme
def update_instruction_memory_display():
    instruction_memory_text.delete("1.0", tk.END)
    instruction_memory_text.tag_config("executed", foreground="black")  # Çalıştırılan talimatlar siyah
    instruction_memory_text.tag_config("skipped", foreground="white")   # Atlanan talimatlar beyaz

    executed_instructions = set()  # Çalıştırılmış talimatların adreslerini tutmak için bir küme
    skipped_indices = set()  # Atlanan talimatların adreslerini tutmak için bir küme

    # Pipeline'daki talimatları belirle
    for stage in pipeline_stages.values():
        if stage != "Empty":
            try:
                instruction_index = instruction_memory.index(stage.strip())
                executed_instructions.add(instruction_index)
            except ValueError:
                continue

    # Atlanan talimatları belirlemek için dallanma kontrolü
    pc_values = [pc]  # Mevcut dallanma sonrası PC değerlerini kaydedin
    for i, instruction in enumerate(instruction_memory):
        if instruction.strip() and (instruction.startswith("beq") or instruction.startswith("bne") or instruction.startswith("j")):
            parts = instruction.split()
            label = parts[-1]  # Etiketin adı
            if label in labels:
                target_index = labels[label]
                if target_index > i:  # İleriye doğru bir dallanma varsa
                    skipped_indices.update(range(i + 1, target_index))
                    pc_values.append(target_index)

    # Talimatları ekle ve renklendir
    for i, instruction in enumerate(instruction_memory):
        if instruction.strip():  # Boş olmayan talimatları işler
            start = f"{i + 1}.0"
            end = f"{i + 1}.end"
            instruction_memory_text.insert(tk.END, f"{i:03}: {instruction}\n")

            if i in executed_instructions or i in pc_values:
                instruction_memory_text.tag_add("executed", start, end)  # Çalıştırılan talimat
            elif i in skipped_indices:
                instruction_memory_text.tag_add("skipped", start, end)  # Atlanan talimat


# GUI bölümünü güncelle
def create_gui():
    global root, input_text, register_labels, memory_text, pipeline_text
    global instruction_memory_text, hazard_text, realistic_pc_value_label, result_label

    root = ttkthemes.ThemedTk()
    root.set_theme("equilux")  # Daha modern koyu tema
    root.title("16-bit RISC Processor Simulator")
    root.configure(bg='#FFB6C1')  # Dış çerçeve pembe arka plan
    
    # Font tanımlamaları
    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(size=11, family="Segoe UI")
    title_font = tkfont.Font(family="Segoe UI", size=13, weight="bold")
    code_font = tkfont.Font(family="Consolas", size=11)
    
    # Ana çerçeve
    main_frame = ttk.Frame(root, padding="15", style='Pink.TFrame')
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Pembe stil tanımlamaları
    style = ttk.Style()
    style.configure('Pink.TFrame', background='#FFB6C1')
    style.configure('Pink.TLabelframe', background='#FFB6C1')
    style.configure('Pink.TLabelframe.Label', background='#FFB6C1', foreground='black')
    # Sol panel (Input ve Kontroller)
    left_panel = ttk.LabelFrame(main_frame, text="Control Panel", padding="10")
    left_panel.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
    
    # Input alanı
    ttk.Label(left_panel, text="Assembly Code Input:", font=title_font).pack(anchor="w", pady=(0,8))
    input_text = tk.Text(left_panel, width=45, height=22, font=code_font, bg='white', fg='#FFB6C1', insertbackground='#FFB6C1')
    input_text.pack(fill=tk.BOTH, expand=True, pady=(0,8))
    
    # Buton çerçevesi - modern tasarım
    button_frame = ttk.Frame(left_panel)
    button_frame.pack(fill=tk.X, pady=8)
    
    button_style = ttk.Style()
    button_style.configure("Action.TButton", font=("Segoe UI", 11))
    
    ttk.Button(button_frame, text="Load Program", command=load_commands, style="Action.TButton").pack(side=tk.LEFT, padx=4)
    ttk.Button(button_frame, text="Step Forward", command=step_pipeline, style="Action.TButton").pack(side=tk.LEFT, padx=4)
    ttk.Button(button_frame, text="Run All", command=run_command, style="Action.TButton").pack(side=tk.LEFT, padx=4)
    
    # Orta panel (Registers ve Memory)
    middle_panel = ttk.Frame(main_frame)
    middle_panel.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
    
    # Register ekranı
    register_frame = ttk.LabelFrame(middle_panel, text="Registers", padding="10")
    register_frame.pack(fill=tk.BOTH, expand=True, pady=(0,8))
    
    register_labels = []
    for name in register_names:
        label = ttk.Label(register_frame, text=f"{name}: 0", font=("Segoe UI", 11))
        label.pack(anchor="w", pady=2)
        register_labels.append(label)
    
    # Memory ekranı
    memory_frame = ttk.LabelFrame(middle_panel, text="Memory", padding="10")
    memory_frame.pack(fill=tk.BOTH, expand=True)
    
    memory_text = tk.Text(memory_frame, width=35, height=15, font=code_font, bg='white', fg='#FFB6C1')
    memory_text.pack(fill=tk.BOTH, expand=True)
    
    # Instruction Memory alanı
    instruction_memory_frame = ttk.LabelFrame(main_frame, text="Instruction Memory (512 bytes)", padding="10")
    instruction_memory_frame.grid(row=0, column=3, padx=8, pady=8, sticky="nsew")
    
    instruction_memory_text = tk.Text(instruction_memory_frame, width=35, height=22, font=code_font, bg='white', fg='#FFB6C1')
    instruction_memory_text.pack(fill=tk.BOTH, expand=True)

    # Sağ panel (Pipeline ve Hazards)
    right_panel = ttk.Frame(main_frame)
    right_panel.grid(row=0, column=2, padx=8, pady=8, sticky="nsew")
    
    # Pipeline ekranı
    pipeline_frame = ttk.LabelFrame(right_panel, text="Pipeline Stages", padding="10")
    pipeline_frame.pack(fill=tk.BOTH, expand=True, pady=(0,8))
    
    pipeline_text = tk.Text(pipeline_frame, width=50, height=8, font=code_font, bg='white', fg='#FFB6C1')
    pipeline_text.pack(fill=tk.BOTH, expand=True)
    
    # Hazard ekranı
    hazard_frame = ttk.LabelFrame(right_panel, text="Hazards", padding="10")
    hazard_frame.pack(fill=tk.BOTH, expand=True)
    
    hazard_text = tk.Text(hazard_frame, width=50, height=8, font=code_font, bg='white', fg='#FFB6C1')
    hazard_text.pack(fill=tk.BOTH, expand=True)
    
    # Alt panel (PC ve Sonuçlar)
    bottom_panel = ttk.Frame(main_frame)
    bottom_panel.grid(row=1, column=0, columnspan=4, pady=8, sticky="ew")
    
    # PC ekranı
    pc_frame = ttk.LabelFrame(bottom_panel, text="Program Counter", padding="10")
    pc_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
    
    realistic_pc_value_label = ttk.Label(pc_frame, text="Realistic PC: 000", font=("Segoe UI", 11))
    realistic_pc_value_label.pack()
    
    # Sonuç mesajı
    result_frame = ttk.LabelFrame(bottom_panel, text="Execution Status", padding="10")
    result_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
    
    result_label = ttk.Label(result_frame, text="Ready to Execute", font=("Segoe UI", 11))
    result_label.pack()
    
    # Grid ağırlıkları
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=1)
    main_frame.grid_columnconfigure(2, weight=1)
    main_frame.grid_columnconfigure(3, weight=1)
    
    return root

# GUI oluşturma ve başlatma
root = create_gui()
root.mainloop()
