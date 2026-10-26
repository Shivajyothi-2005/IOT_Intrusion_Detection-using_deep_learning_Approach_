import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)
    
    # Theme Colors
    c_dark_slate = RGBColor(15, 23, 42)    # #0F172A
    c_teal = RGBColor(13, 148, 136)       # #0D9488
    c_light_gray = RGBColor(248, 250, 252) # #F8FAFC
    c_white = RGBColor(255, 255, 255)
    c_text_dark = RGBColor(15, 23, 42)
    c_text_light = RGBColor(241, 245, 249)
    c_accent_red = RGBColor(185, 28, 28)
    
    blank_layout = prs.slide_layouts[6]
    
    # Helper to add standard slide background and header accent
    def add_slide_base(title_text):
        slide = prs.slides.add_slide(blank_layout)
        # Background color: Light Gray
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = c_light_gray
        
        # Top accent bar (Teal, 0.1 inch height)
        slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0), Inches(0), Inches(13.33), Inches(0.12)
        ).fill.solid()
        slide.shapes[-1].fill.fore_color.rgb = c_teal
        slide.shapes[-1].line.color.rgb = c_teal
        
        # Slide Header Title
        title_box = slide.shapes.add_textbox(Inches(0.75), Inches(0.4), Inches(11.83), Inches(0.8))
        tf = title_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title_text.upper()
        p.font.name = "Helvetica"
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = c_dark_slate
        
        # Subtitle separator line
        sep = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0.75), Inches(1.15), Inches(11.83), Inches(0.02)
        )
        sep.fill.solid()
        sep.fill.fore_color.rgb = c_teal
        sep.line.color.rgb = c_teal
        
        return slide

    # ==========================================
    # SLIDE 1: TITLE SLIDE (Dark Theme)
    # ==========================================
    slide1 = prs.slides.add_slide(blank_layout)
    fill1 = slide1.background.fill
    fill1.solid()
    fill1.fore_color.rgb = c_dark_slate
    
    # Left: Title and metadata
    txt_box = slide1.shapes.add_textbox(Inches(0.8), Inches(1.2), Inches(6.5), Inches(5.0))
    tf1 = txt_box.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = tf1.margin_right = tf1.margin_bottom = 0
    
    p_sub = tf1.paragraphs[0]
    p_sub.text = "A MINI-PROJECT PRESENTATION"
    p_sub.font.name = "Helvetica"
    p_sub.font.size = Pt(12)
    p_sub.font.bold = True
    p_sub.font.color.rgb = c_teal
    p_sub.space_after = Pt(15)
    
    p_title = tf1.add_paragraph()
    p_title.text = "Cyber Security Threats Detection in IoT using Deep Learning"
    p_title.font.name = "Helvetica"
    p_title.font.size = Pt(36)
    p_title.font.bold = True
    p_title.font.color.rgb = c_white
    p_title.space_after = Pt(30)
    
    p_meta = tf1.add_paragraph()
    p_meta.text = "Submitted by:\n• B. Shiva Jyothi (1608-23-733-162)\n• S. Swecha (1608-23-733-313)\n• G. Varshith (1608-23-733-314)\n\nUnder the Guidance of:\n• Mrs. Rama Lakshmi (Assistant Professor)"
    p_meta.font.name = "Helvetica"
    p_meta.font.size = Pt(14)
    p_meta.font.color.rgb = RGBColor(194, 205, 217)
    
    # Right: Cover Image
    img_path = "iot_security_cover.png"
    if os.path.exists(img_path):
        slide1.shapes.add_picture(img_path, Inches(7.5), Inches(1.5), width=Inches(5.0), height=Inches(4.5))

    # ==========================================
    # SLIDE 2: ABSTRACT & PROBLEM STATEMENT
    # ==========================================
    slide2 = add_slide_base("Abstract & Problem Statement")
    
    # Left: Abstract text
    left_box = slide2.shapes.add_textbox(Inches(0.75), Inches(1.6), Inches(5.8), Inches(5.0))
    tf2_l = left_box.text_frame
    tf2_l.word_wrap = True
    p_abs_title = tf2_l.paragraphs[0]
    p_abs_title.text = "Project Abstract"
    p_abs_title.font.name = "Helvetica"
    p_abs_title.font.size = Pt(20)
    p_abs_title.font.bold = True
    p_abs_title.font.color.rgb = c_teal
    p_abs_title.space_after = Pt(10)
    
    p_abs_text = tf2_l.add_paragraph()
    p_abs_text.text = (
        "IoT devices are connected everywhere but lack the CPU power to run traditional firewalls, making them targets for DDoS, Port Scans, and brute-force logins.\n\n"
        "This project presents a Real-Time Cybersecurity Threat Detection System. We implement a PyTorch 1D Convolutional Neural Network (1D-CNN) that sniffs network flows, classifies threat classes, and streams results instantly via WebSockets to an interactive SVG dashboard."
    )
    p_abs_text.font.name = "Helvetica"
    p_abs_text.font.size = Pt(14)
    p_abs_text.font.color.rgb = c_text_dark
    
    # Right: Problem Statement Callout Card
    card = slide2.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(7.2), Inches(1.6), Inches(5.38), Inches(4.8)
    )
    card.fill.solid()
    card.fill.fore_color.rgb = RGBColor(254, 242, 242) # Hex #FEF2F2
    card.line.color.rgb = RGBColor(252, 165, 165)     # Hex #FCA5A5
    
    card_text_box = slide2.shapes.add_textbox(Inches(7.4), Inches(1.8), Inches(5.0), Inches(4.4))
    tf2_r = card_text_box.text_frame
    tf2_r.word_wrap = True
    p_card_title = tf2_r.paragraphs[0]
    p_card_title.text = "THE CYBER SECURITY PROBLEM"
    p_card_title.font.name = "Helvetica"
    p_card_title.font.size = Pt(18)
    p_card_title.font.bold = True
    p_card_title.font.color.rgb = c_accent_red
    p_card_title.space_after = Pt(12)
    
    p_card_body = tf2_r.add_paragraph()
    p_card_body.text = (
        "• Hardened endpoints cannot run on low-power IoT devices.\n\n"
        "• Existing signature matching gateway systems (e.g., Snort) completely miss zero-day exploits.\n\n"
        "• Traditional Flask and MySQL logging configurations block runtime threads and suffer from high visual latency."
    )
    p_card_body.font.name = "Helvetica"
    p_card_body.font.size = Pt(14)
    p_card_body.font.color.rgb = c_text_dark

    # ==========================================
    # SLIDE 3: PROJECT OBJECTIVES
    # ==========================================
    slide3 = add_slide_base("Project Objectives")
    
    obj_box = slide3.shapes.add_textbox(Inches(0.75), Inches(1.8), Inches(11.83), Inches(4.5))
    tf3 = obj_box.text_frame
    tf3.word_wrap = True
    
    objectives = [
        ("Real-time Ingestion", "Sniff packet headers asynchronously at the network gateway without impeding local routing latencies."),
        ("Zero-Privilege Polling", "Provide a lightweight telemetry client agent that tracks connection throughput using sockets without requiring system root/admin privileges."),
        ("Applied Machine Learning", "Run a 1D Convolutional Neural Network (1D-CNN) inference in PyTorch to classify anomalous threat features in under 2ms."),
        ("Instant Alert Dashboard", "Broadcast flows asynchronously via WebSockets to update an interactive network map using color-coded particle paths (green = safe, red = threat).")
    ]
    
    for idx, (title, desc) in enumerate(objectives):
        p_title = tf3.add_paragraph() if idx > 0 else tf3.paragraphs[0]
        p_title.text = f"• {title}:"
        p_title.font.name = "Helvetica"
        p_title.font.size = Pt(18)
        p_title.font.bold = True
        p_title.font.color.rgb = c_teal
        p_title.space_after = Pt(2)
        
        p_desc = tf3.add_paragraph()
        p_desc.text = desc
        p_desc.font.name = "Helvetica"
        p_desc.font.size = Pt(14)
        p_desc.font.color.rgb = c_text_dark
        p_desc.space_after = Pt(15)

    # ==========================================
    # SLIDE 4: SYSTEM REQUIREMENT SPECIFICATION
    # ==========================================
    slide4 = add_slide_base("System Requirement Specification")
    
    # Left column: Software Requirements
    sw_box = slide4.shapes.add_textbox(Inches(0.75), Inches(1.6), Inches(5.5), Inches(5.0))
    tf4_l = sw_box.text_frame
    tf4_l.word_wrap = True
    p_sw_title = tf4_l.paragraphs[0]
    p_sw_title.text = "Software Specifications"
    p_sw_title.font.name = "Helvetica"
    p_sw_title.font.size = Pt(20)
    p_sw_title.font.bold = True
    p_sw_title.font.color.rgb = c_teal
    p_sw_title.space_after = Pt(10)
    
    sw_points = [
        "Operating System: Windows 10/11 or Ubuntu Linux 20.04+",
        "Language Engine: Python 3.8+ runtime environments",
        "Deep Learning: PyTorch 2.1+ framework CPU/GPU wheels",
        "API Core: FastAPI with Uvicorn async ASGI server",
        "Libraries: Scapy (packet sniffer), psutil (CPU monitor), NumPy",
        "UI Technologies: HTML5, CSS3 Custom Theme, Vanilla ES6 JavaScript"
    ]
    for pt in sw_points:
        p_pt = tf4_l.add_paragraph()
        p_pt.text = f"• {pt}"
        p_pt.font.name = "Helvetica"
        p_pt.font.size = Pt(14)
        p_pt.font.color.rgb = c_text_dark
        p_pt.space_after = Pt(8)
        
    # Right column: Hardware Requirements
    hw_box = slide4.shapes.add_textbox(Inches(7.0), Inches(1.6), Inches(5.5), Inches(5.0))
    tf4_r = hw_box.text_frame
    tf4_r.word_wrap = True
    p_hw_title = tf4_r.paragraphs[0]
    p_hw_title.text = "Hardware Specifications"
    p_hw_title.font.name = "Helvetica"
    p_hw_title.font.size = Pt(20)
    p_hw_title.font.bold = True
    p_hw_title.font.color.rgb = c_teal
    p_hw_title.space_after = Pt(10)
    
    hw_points = [
        "Gateway Processor: Intel Core i5 or AMD Ryzen 5 CPU (or equivalent)",
        "System memory: 8 GB RAM minimum (16 GB recommended)",
        "Hard Disk storage: 10 GB free space for python modules and weights",
        "Network Telemetry Clients: Laptops, servers, ESP32 boards, or microcontrollers"
    ]
    for pt in hw_points:
        p_pt = tf4_r.add_paragraph()
        p_pt.text = f"• {pt}"
        p_pt.font.name = "Helvetica"
        p_pt.font.size = Pt(14)
        p_pt.font.color.rgb = c_text_dark
        p_pt.space_after = Pt(8)

    # ==========================================
    # SLIDE 5: SYSTEM DESIGN - COMPARISON
    # ==========================================
    slide5 = add_slide_base("System Design Comparison")
    
    # Text introduction
    intro_box = slide5.shapes.add_textbox(Inches(0.75), Inches(1.4), Inches(11.83), Inches(0.6))
    p_intro = intro_box.text_frame.paragraphs[0]
    p_intro.text = "How the proposed deep learning system compares to traditional architectures:"
    p_intro.font.name = "Helvetica"
    p_intro.font.size = Pt(14)
    p_intro.font.color.rgb = c_text_dark
    
    # Table layout
    rows = 4
    cols = 2
    left = Inches(0.75)
    top = Inches(2.1)
    width = Inches(11.83)
    height = Inches(4.5)
    
    table_shape = slide5.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table
    
    # Column Widths
    table.columns[0].width = Inches(5.91)
    table.columns[1].width = Inches(5.92)
    
    # Headers
    table.cell(0, 0).text = "TRADITIONAL INTRUSION DETECTORS"
    table.cell(0, 1).text = "PROPOSED DEEP LEARNING SYSTEM"
    
    # Data Rows
    table.cell(1, 0).text = "Static signature lists block known threats but fail completely against zero-day custom exploits."
    table.cell(1, 1).text = "1D Convolutional Neural Network learns spatial packet features to classify threats dynamically."
    
    table.cell(2, 0).text = "Relational database writes (Flask + MySQL) block main execution threads under high traffic."
    table.cell(2, 1).text = "Asynchronous state manager caches logs in-memory and saves files to disk without thread blocks."
    
    table.cell(3, 0).text = "Dashboards require page refresh tags (polling), introducing lag and alert delays."
    table.cell(3, 1).text = "WebSockets push predictions asynchronously to dashboard nodes in under 2 milliseconds."
    
    # Styling Table Cells
    for r_idx in range(rows):
        for c_idx in range(cols):
            cell = table.cell(r_idx, c_idx)
            cell.margin_left = cell.margin_right = cell.margin_top = cell.margin_bottom = Inches(0.15)
            # Format text
            for p in cell.text_frame.paragraphs:
                p.font.name = "Helvetica"
                p.font.size = Pt(14)
                if r_idx == 0:
                    p.font.bold = True
                    p.font.size = Pt(16)
                    p.font.color.rgb = c_white
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = c_teal
                else:
                    p.font.color.rgb = c_text_dark
                    cell.fill.solid()
                    if r_idx % 2 == 1:
                        cell.fill.fore_color.rgb = c_light_gray
                    else:
                        cell.fill.fore_color.rgb = c_white

    # ==========================================
    # SLIDE 6: SYSTEM ARCHITECTURE
    # ==========================================
    slide6 = add_slide_base("System Architecture")
    
    # Left: Explanation of Flow
    flow_box = slide6.shapes.add_textbox(Inches(0.75), Inches(1.6), Inches(5.5), Inches(5.0))
    tf6_l = flow_box.text_frame
    tf6_l.word_wrap = True
    p_flow_title = tf6_l.paragraphs[0]
    p_flow_title.text = "Telemetries Processing Flow"
    p_flow_title.font.name = "Helvetica"
    p_flow_title.font.size = Pt(20)
    p_flow_title.font.bold = True
    p_flow_title.font.color.rgb = c_teal
    p_flow_title.space_after = Pt(10)
    
    flow_steps = [
        "Client Sniffer: Captures packets, extracts 14-features, and posts flow JSON every 2 seconds.",
        "ASGI Gateway: FastAPI validates schema models, passing inputs to the inference engine.",
        "1D-CNN Inference: Scales features to [0,1], checks Conv1D weights, and predicts anomaly probabilities.",
        "Rule Overlay: Heuristics checks target ports to suppress false alerts on HTTP/HTTPS.",
        "Dashboard Broadcast: WebSockets push alerts, lighting up SVG nodes (green/red) in real-time."
    ]
    for step in flow_steps:
        p_step = tf6_l.add_paragraph()
        p_step.text = f"• {step}"
        p_step.font.name = "Helvetica"
        p_step.font.size = Pt(13)
        p_step.font.color.rgb = c_text_dark
        p_step.space_after = Pt(10)
        
    # Right: Simple Flow Box Diagram (drawn with slides shapes)
    right_box = slide6.shapes.add_textbox(Inches(6.8), Inches(1.5), Inches(5.8), Inches(5.0))
    tf6_r = right_box.text_frame
    tf6_r.word_wrap = True
    
    arch_str = (
        "                    [ IoT Telemetry Client ]\n"
        "                               |\n"
        "                               | HTTP POST\n"
        "                               v\n"
        "                    [ FastAPI ASGI Server ]\n"
        "                               |\n"
        "                               | normalizes flow\n"
        "                               v\n"
        "                    [ PyTorch 1D-CNN Model ]\n"
        "                               |\n"
        "                               | checks bypass rules\n"
        "                               v\n"
        "                    [ Low-blocking state DB ]\n"
        "                               |\n"
        "                               | WebSockets push\n"
        "                               v\n"
        "                    [ HTML5 Live Web Map ]"
    )
    p_arch = tf6_r.paragraphs[0]
    p_arch.text = arch_str
    p_arch.font.name = "Courier New"
    p_arch.font.size = Pt(13)
    p_arch.font.bold = True
    p_arch.font.color.rgb = c_dark_slate
    
    # Format box container for ASCII diagram
    card6 = slide6.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(6.6), Inches(1.5), Inches(6.0), Inches(4.8)
    )
    card6.fill.solid()
    card6.fill.fore_color.rgb = c_light_gray
    card6.line.color.rgb = c_border_rgb = RGBColor(226, 232, 240)
    # Re-order shape stack so text box is on top of container
    slide6.shapes[-2]._element.getparent().append(slide6.shapes[-2]._element) # Textbox to front
    slide6.shapes[-1]._element.getparent().append(slide6.shapes[-1]._element) # Textbox contents to front

    # ==========================================
    # SLIDE 7: PROJECT METHODOLOGIES
    # ==========================================
    slide7 = add_slide_base("Project Methodologies")
    
    meth_box = slide7.shapes.add_textbox(Inches(0.75), Inches(1.6), Inches(11.83), Inches(5.0))
    tf7 = meth_box.text_frame
    tf7.word_wrap = True
    
    meths = [
        ("1. Data Aggregation", "Packets are sniffed and aggregated over sliding 2-second windows to compute flows."),
        ("2. Normalization Scaling", "Applies min-max scaling parameters to convert raw data into neural inputs [0, 1]."),
        ("3. 1D Convolution Neural Net", "Conv1D layer extracts local temporal packet patterns; MaxPool1D selects robust features; Linear layers output logits."),
        ("4. Hybrid Decision Engine", "Combines deep learning probabilities with destination port checks to prevent false alarms on common services (DNS, Web)."),
        ("5. Event-Driven Updates", "FastAPI background tasks save database caches asynchronously, streaming alerts over WebSockets.")
    ]
    for idx, (title, desc) in enumerate(meths):
        p_title = tf7.add_paragraph() if idx > 0 else tf7.paragraphs[0]
        p_title.text = title
        p_title.font.name = "Helvetica"
        p_title.font.size = Pt(16)
        p_title.font.bold = True
        p_title.font.color.rgb = c_teal
        p_title.space_after = Pt(2)
        
        p_desc = tf7.add_paragraph()
        p_desc.text = desc
        p_desc.font.name = "Helvetica"
        p_desc.font.size = Pt(13)
        p_desc.font.color.rgb = c_text_dark
        p_desc.space_after = Pt(10)

    # ==========================================
    # SLIDE 8: CORE CODE IMPLEMENTATION
    # ==========================================
    slide8 = add_slide_base("Core Code Implementation")
    
    code_box = slide8.shapes.add_textbox(Inches(0.75), Inches(1.5), Inches(11.83), Inches(5.0))
    tf8 = code_box.text_frame
    tf8.word_wrap = True
    
    p_code_title = tf8.paragraphs[0]
    p_code_title.text = "Inference Engine with Port Heuristics Overlay (backend/model.py)"
    p_code_title.font.name = "Helvetica"
    p_code_title.font.size = Pt(16)
    p_code_title.font.bold = True
    p_code_title.font.color.rgb = c_teal
    p_code_title.space_after = Pt(8)
    
    code_str = (
        "def predict_threat(raw_features):\n"
        "    # 1. Scale input features into normal range [0, 1]\n"
        "    norm_features = normalize_features(raw_features)\n"
        "    input_tensor = torch.tensor(norm_features).unsqueeze(0).unsqueeze(0)\n\n"
        "    # 2. Run PyTorch Conv1D forward propagation\n"
        "    with torch.no_grad():\n"
        "        logits = model(input_tensor)\n"
        "        probabilities = torch.softmax(logits, dim=1).squeeze().numpy()\n"
        "    class_id = int(np.argmax(probabilities))\n\n"
        "    # 3. Apply hybrid heuristics overlay to suppress false alarms on HTTP/HTTPS\n"
        "    dst_port, packet_rate = raw_features[1], raw_features[6]\n"
        "    if dst_port == 443 and class_id != 0 and packet_rate < 150:\n"
        "        class_id = 0  # Reclassify as Normal\n"
        "    return class_id, CLASSES[class_id]"
    )
    p_code = tf8.add_paragraph()
    p_code.text = code_str
    p_code.font.name = "Courier New"
    p_code.font.size = Pt(11)
    p_code.font.color.rgb = c_dark_slate
    p_code.space_before = Pt(5)
    
    # Format code container box
    card8 = slide8.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.75), Inches(1.9), Inches(11.83), Inches(4.5)
    )
    card8.fill.solid()
    card8.fill.fore_color.rgb = c_light_gray
    card8.line.color.rgb = RGBColor(226, 232, 240)
    slide8.shapes[-2]._element.getparent().append(slide8.shapes[-2]._element)
    slide8.shapes[-1]._element.getparent().append(slide8.shapes[-1]._element)

    # ==========================================
    # SLIDE 9: EXPERIMENTAL RESULTS
    # ==========================================
    slide9 = add_slide_base("Experimental Results")
    
    # Left: Text results and stats
    res_box = slide9.shapes.add_textbox(Inches(0.75), Inches(1.6), Inches(5.8), Inches(5.0))
    tf9_l = res_box.text_frame
    tf9_l.word_wrap = True
    p_res_title = tf9_l.paragraphs[0]
    p_res_title.text = "Ingestion & UI Validation"
    p_res_title.font.name = "Helvetica"
    p_res_title.font.size = Pt(20)
    p_res_title.font.bold = True
    p_res_title.font.color.rgb = c_teal
    p_res_title.space_after = Pt(10)
    
    res_points = [
        "Telemetry posts validated successfully using Pydantic classes.",
        "Model prediction is extremely fast, running on CPU in under 2ms.",
        "Destination port check rules completely bypass false positives on standard web browsing.",
        "WebSocket broadcast loads paths dynamically in the SVG map (green = safe, red = attack).",
        "Pruning endpoints successfully clear offline devices dynamically."
    ]
    for pt in res_points:
        p_pt = tf9_l.add_paragraph()
        p_pt.text = f"• {pt}"
        p_pt.font.name = "Helvetica"
        p_pt.font.size = Pt(14)
        p_pt.font.color.rgb = c_text_dark
        p_pt.space_after = Pt(8)
        
    # Right: Dashboard image mockup
    img_path2 = "iot_security_dashboard.png"
    if os.path.exists(img_path2):
        slide9.shapes.add_picture(img_path2, Inches(7.0), Inches(1.8), width=Inches(5.5), height=Inches(3.8))

    # ==========================================
    # SLIDE 10: CONCLUSION & FUTURE SCOPE
    # ==========================================
    slide10 = add_slide_base("Conclusion & Future Scope")
    
    # Left: Conclusion
    con_box = slide10.shapes.add_textbox(Inches(0.75), Inches(1.6), Inches(5.8), Inches(5.0))
    tf10_l = con_box.text_frame
    tf10_l.word_wrap = True
    p_con_title = tf10_l.paragraphs[0]
    p_con_title.text = "Project Conclusion"
    p_con_title.font.name = "Helvetica"
    p_con_title.font.size = Pt(20)
    p_con_title.font.bold = True
    p_con_title.font.color.rgb = c_teal
    p_con_title.space_after = Pt(10)
    
    p_con_text = tf10_l.add_paragraph()
    p_con_text.text = (
        "• The system successfully implements real-time gateway intrusion monitoring for diverse IoT nodes.\n\n"
        "• Decoupling database operations via memory caches allows the FastAPI backend to ingest high-speed packets without thread locks.\n\n"
        "• Combining Conv1D neural predictions with heuristic overlays secures standard network services (zero false alarms on HTTPS)."
    )
    p_con_text.font.name = "Helvetica"
    p_con_text.font.size = Pt(14)
    p_con_text.font.color.rgb = c_text_dark
    
    # Right: Future Scope
    fut_box = slide10.shapes.add_textbox(Inches(7.0), Inches(1.6), Inches(5.5), Inches(5.0))
    tf10_r = fut_box.text_frame
    tf10_r.word_wrap = True
    p_fut_title = tf10_r.paragraphs[0]
    p_fut_title.text = "Future Extensions"
    p_fut_title.font.name = "Helvetica"
    p_fut_title.font.size = Pt(20)
    p_fut_title.font.bold = True
    p_fut_title.font.color.rgb = c_teal
    p_fut_title.space_after = Pt(10)
    
    p_fut_text = tf10_r.add_paragraph()
    p_fut_text.text = (
        "• Edge Inference: Exporting PyTorch weights to ONNX/TensorFlow Lite to run models directly on microcontrollers (e.g., ESP32).\n\n"
        "• Extended Datasets: Retraining models on dynamic industrial IoT datasets containing ARP spoofing and botnet vectors.\n\n"
        "• Active Intervention: Integrating client-side OS firewall APIs to automatically drop packet payloads from blacklisted IP nodes."
    )
    p_fut_text.font.name = "Helvetica"
    p_fut_text.font.size = Pt(14)
    p_fut_text.font.color.rgb = c_text_dark

    # ==========================================
    # SLIDE 11: REFERENCES
    # ==========================================
    slide11 = add_slide_base("References & Bibliography")
    
    ref_box = slide11.shapes.add_textbox(Inches(0.75), Inches(1.8), Inches(11.83), Inches(4.5))
    tf11 = ref_box.text_frame
    tf11.word_wrap = True
    
    refs = [
        "[1] FastAPI Development Team, \"FastAPI Web Framework API Reference Manual,\" Pallets Projects, 2026. Available: https://fastapi.tiangolo.com/",
        "[2] PyTorch Contributors, \"PyTorch Documentation: Deep Neural Architectures and Conv1D Kernels,\" Linux Foundation, 2025. Available: https://pytorch.org/docs/",
        "[3] F. Chollet, \"Keras 1D Convolution Layers: Temporal Sequence Processing,\" Keras Team, 2024. Available: https://keras.io/api/layers/",
        "[4] P. Biondi, \"Scapy Packet Sniffing & Manipulation Documentation,\" Scapy Project, 2025. Available: https://scapy.net/",
        "[5] S. Khraisat et al., \"Survey of Intrusion Detection Systems: Techniques, Datasets, and Challenges,\" Cybersecurity Journal, 2019."
    ]
    for idx, ref in enumerate(refs):
        p_ref = tf11.add_paragraph() if idx > 0 else tf11.paragraphs[0]
        p_ref.text = ref
        p_ref.font.name = "Helvetica"
        p_ref.font.size = Pt(14)
        p_ref.font.color.rgb = c_text_dark
        p_ref.space_after = Pt(15)
        
    prs.save("Mini_Project_Report_Creative.pptx")
    print("[+] Successfully compiled Mini_Project_Report_Creative.pptx!")

if __name__ == "__main__":
    create_presentation()
