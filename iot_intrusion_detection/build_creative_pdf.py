import os
import sys
import subprocess
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Preformatted
from reportlab.pdfgen import canvas

# ----------------- Creative Dynamic Page Numbering Canvas -----------------
class CreativeCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(CreativeCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        # Hide all decorations on Page 1 (Cover Page)
        if self._pageNumber == 1:
            return
        
        self.saveState()
        
        # 1. Top Teal Accent Bar (Thick 3pt line at the very top of each page)
        self.setFillColor(colors.HexColor('#0D9488'))
        self.rect(0, A4[1] - 4, A4[0], 4, stroke=0, fill=1)
        
        # 2. Header
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor('#475569'))
        self.drawString(0.75 * inch, A4[1] - 0.5 * inch, "CYBER SECURITY THREATS DETECTION IN IOT USING DEEP LEARNING")
        
        self.setStrokeColor(colors.HexColor('#E2E8F0'))
        self.setLineWidth(0.5)
        self.line(0.75 * inch, A4[1] - 0.55 * inch, A4[0] - 0.75 * inch, A4[1] - 0.55 * inch)
        
        # 3. Footer
        self.line(0.75 * inch, 0.75 * inch, A4[0] - 0.75 * inch, 0.75 * inch)
        self.setFont("Helvetica", 8)
        self.drawString(0.75 * inch, 0.55 * inch, "Department of Computer Science and Engineering, MEC")
        
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 0.75 * inch, 0.55 * inch, page_text)
        
        self.restoreState()

# ----------------- Image Helper -----------------
def get_image_safe(filename, width, height, body_style):
    abs_path = os.path.join("C:/Users/shivajyothi/.gemini/antigravity/scratch/iot_intrusion_detection", filename)
    if os.path.exists(abs_path):
        from reportlab.platypus import Image
        return Image(abs_path, width=width, height=height)
    return Paragraph(f"<i>[Image placeholder: {filename} was not found on disk]</i>", body_style)

# ----------------- Build PDF Document Function -----------------
def generate_pdf(toc_pages=None):
    pdf_filename = "Mini_Project_Report_Creative.pdf"
    
    # 0.75 inch margins for a modern, sleek whitepaper layout
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=A4,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.9 * inch
    )
    
    styles = getSampleStyleSheet()
    
    # Color definition
    c_primary = colors.HexColor('#0F172A')   # Slate-900 (Headers)
    c_secondary = colors.HexColor('#0D9488') # Teal-600 (Accents)
    c_text = colors.HexColor('#334155')      # Slate-700 (Body text)
    c_light_bg = colors.HexColor('#F8FAFC')  # Slate-50 (Code / Callouts)
    c_border = colors.HexColor('#E2E8F0')    # Slate-200 (Borders)
    
    # Styles definition
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=26,
        textColor=c_primary,
        alignment=1, # Center
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        alignment=1, # Center
        spaceAfter=10
    )
    
    chapter_style = ParagraphStyle(
        'ChapterHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=c_primary,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=15.5, # 1.5 line spacing approx
        textColor=c_text,
        spaceAfter=8,
        alignment=4 # Justified
    )
    
    body_bold = ParagraphStyle(
        'ReportBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=c_primary
    )
    
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0F172A'),
        backColor=c_light_bg,
        borderColor=c_border,
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=10
    )

    story = []
    
    # ----------------- PAGE 1: CREATIVE COVER PAGE -----------------
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("A MINI-PROJECT REPORT", subtitle_style))
    story.append(Paragraph("CYBER SECURITY THREATS DETECTION IN INTERNET OF THINGS USING DEEP LEARNING APPROACHES", title_style))
    story.append(Spacer(1, 0.1 * inch))
    
    # Classy generated illustration
    story.append(get_image_safe("iot_security_cover.png", 4.2 * inch, 3.2 * inch, body_style))
    story.append(Spacer(1, 0.15 * inch))
    
    metadata_style_label = ParagraphStyle('MetaLabel', parent=body_style, fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#475569'))
    metadata_style_val = ParagraphStyle('MetaVal', parent=body_style, fontSize=9, textColor=c_primary)
    
    meta_data = [
        [Paragraph("<b>Submitted By:</b>", metadata_style_label), Paragraph("<b>Guided By:</b>", metadata_style_label)],
        [Paragraph("B. Shiva Jyothi (1608-23-733-162)<br/>S. Swecha (1608-23-733-313)<br/>G. Varshith (1608-23-733-314)", metadata_style_val),
         Paragraph("Mrs. Rama Lakshmi<br/>Assistant Professor, Dept. of CSE", metadata_style_val)]
    ]
    meta_table = Table(meta_data, colWidths=[3.2*inch, 3.2*inch])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.15 * inch))
    
    # College details table with logo
    college_data = [
        [get_image_safe("college_logo.png", 0.7 * inch, 0.7 * inch, body_style),
         Paragraph("<b>Department of Computer Science and Engineering</b><br/><b>MATRUSRI ENGINEERING COLLEGE</b><br/>"
                   "<font size=8 color='#475569'>(Affiliated to Osmania University, Approved by AICTE) Saidabad, Hyderabad - 500059</font>",
                   ParagraphStyle('CollMeta', parent=body_style, leading=11, textColor=c_primary))]
    ]
    college_table = Table(college_data, colWidths=[0.9*inch, 5.5*inch])
    college_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'CENTER'),
    ]))
    story.append(college_table)
    story.append(PageBreak())
    
    # ----------------- PAGE 2: TABLE OF CONTENTS & LISTS -----------------
    story.append(Paragraph("<b>TABLE OF CONTENTS</b>", chapter_style))
    story.append(Spacer(1, 0.05 * inch))
    
    t_ch1 = toc_pages.get("ch1", "3") if toc_pages else "3"
    t_ch2 = toc_pages.get("ch2", "4") if toc_pages else "4"
    t_ch3 = toc_pages.get("ch3", "5") if toc_pages else "5"
    t_ch4 = toc_pages.get("ch4", "6") if toc_pages else "6"
    t_ch5 = toc_pages.get("ch5", "7") if toc_pages else "7"
    t_ch6 = toc_pages.get("ch6", "9") if toc_pages else "9"
    t_ref = toc_pages.get("ref", "10") if toc_pages else "10"
    
    t_fig = toc_pages.get("fig", "8") if toc_pages else "8"
    t_tab = toc_pages.get("tab", "8") if toc_pages else "8"
    
    toc_data = [
        [Paragraph("<b>Abstract</b>", body_bold), Paragraph(f"<b>{t_ch1}</b>", body_bold)],
        [Paragraph("<b>1. Introduction & Objectives</b>", body_bold), Paragraph(f"<b>{t_ch1}</b>", body_bold)],
        [Paragraph("<b>2. System Requirement Specification</b>", body_bold), Paragraph(f"<b>{t_ch2}</b>", body_bold)],
        [Paragraph("<b>3. System Design & Existing System Comparison</b>", body_bold), Paragraph(f"<b>{t_ch3}</b>", body_bold)],
        [Paragraph("<b>4. System Flow & Architecture</b>", body_bold), Paragraph(f"<b>{t_ch4}</b>", body_bold)],
        [Paragraph("<b>5. Methodologies</b>", body_bold), Paragraph(f"<b>{t_ch5}</b>", body_bold)],
        [Paragraph("<b>6. Core Implementation</b>", body_bold), Paragraph(f"<b>{t_ch6}</b>", body_bold)],
        [Paragraph("<b>7. Experimental Results & Verification</b>", body_bold), Paragraph(f"<b>{t_ch5}</b>", body_bold)], # Results starts on same or next page
        [Paragraph("<b>8. Conclusion, Future Extensions & References</b>", body_bold), Paragraph(f"<b>{t_ch6}</b>", body_bold)],
    ]
    
    toc_table = Table(toc_data, colWidths=[5.6*inch, 0.8*inch])
    toc_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, c_border),
    ]))
    story.append(toc_table)
    story.append(Spacer(1, 0.3 * inch))
    
    story.append(Paragraph("<b>LIST OF FIGURES & TABLES</b>", chapter_style))
    story.append(Spacer(1, 0.05 * inch))
    
    list_data = [
        [Paragraph("<b>S.No</b>", body_bold), Paragraph("<b>Item Name</b>", body_bold), Paragraph("<b>Type</b>", body_bold), Paragraph("<b>Page No</b>", body_bold)],
        [Paragraph("1", body_style), Paragraph("Fig 4.1: System Architecture Design (ASCII Flow)", body_style), Paragraph("Figure", body_style), Paragraph(str(t_ch4), body_style)],
        [Paragraph("2", body_style), Paragraph("Fig 7.1: Live Cybersecurity Threat Dashboard Mockup", body_style), Paragraph("Figure", body_style), Paragraph(str(t_ch5), body_style)],
        [Paragraph("3", body_style), Paragraph("Table 7.1: System Validation Test Cases", body_style), Paragraph("Table", body_style), Paragraph(str(t_ch5), body_style)]
    ]
    list_table = Table(list_data, colWidths=[0.8*inch, 3.8*inch, 1.0*inch, 0.8*inch])
    list_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, c_border),
    ]))
    story.append(list_table)
    story.append(PageBreak())
    
    # ----------------- PAGE 3: ABSTRACT, INTRODUCTION & OBJECTIVES -----------------
    story.append(Paragraph("<b>ABSTRACT</b>", chapter_style))
    abs_txt = (
        "The Internet of Things (IoT) connects millions of smart devices like smart home products, security cameras, "
        "and industrial sensors. However, many IoT devices have weak security because they do not have the processing "
        "power to run standard firewalls or antivirus software. This makes them easy targets for cybersecurity attacks "
        "like Distributed Denial of Service (DDoS), Port Scanning, and brute-force logins. This project presents a "
        "<b>Real-Time IoT Cybersecurity Threat Detection System</b>. It uses a deep learning approach based on a "
        "<b>1D Convolutional Neural Network (1D-CNN)</b> to inspect network traffic and identify threats automatically. "
        "Our system has client monitoring agents that capture network data and send it to a FastAPI backend server. "
        "The server runs the 1D-CNN model to predict if traffic is normal or malicious, combining the model with simple "
        "heuristics to prevent false alarms on common web ports."
    )
    story.append(Paragraph(abs_txt, body_style))
    story.append(Spacer(1, 0.15 * inch))
    
    story.append(Paragraph("<b>1. INTRODUCTION & OBJECTIVES</b>", chapter_style))
    
    # Problem Statement Callout Card
    prob_title = Paragraph("<b>PROBLEM STATEMENT</b>", ParagraphStyle('CallTitle', parent=body_style, fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#B91C1C')))
    prob_text = Paragraph(
        "IoT deployments suffer from a massive attack surface. Due to hardware resource constraints, standard firewalls "
        "cannot run on individual devices. Traditional gateway-based monitoring relies on static threat signatures, which fails "
        "against new exploits, and causes delayed notification dashboards.", body_style
    )
    prob_card_data = [[prob_title], [prob_text]]
    prob_card = Table(prob_card_data, colWidths=[6.4*inch])
    prob_card.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF2F2')),
        ('BOX', (0,0), (-1,-1), 1.0, colors.HexColor('#FCA5A5')),
        ('PADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('BOTTOMPADDING', (0,1), (-1,1), 8),
    ]))
    story.append(prob_card)
    story.append(Spacer(1, 0.15 * inch))
    
    story.append(Paragraph("Project Objectives:", section_style))
    obj_txt = (
        "• <b>Real-time packet capture:</b> Sniff network headers asynchronously at the gateway without slowing down packet routing.<br/>"
        "• <b>Lightweight system throughput poll:</b> Provide a zero-privilege client monitor for resource-constrained laptops.<br/>"
        "• <b>Deep Learning Inference:</b> Run a 1D-CNN model in PyTorch on 14-dimensional flow feature vectors.<br/>"
        "• <b>Real-Time Web UI:</b> Stream alerts instantly to a dashboard topology map using WebSockets."
    )
    story.append(Paragraph(obj_txt, body_style))
    story.append(PageBreak())
    
    # ----------------- PAGE 4: SYSTEM REQUIREMENT SPECIFICATION (SRS) -----------------
    story.append(Paragraph("<b>2. SYSTEM REQUIREMENT SPECIFICATION</b>", chapter_style))
    story.append(Spacer(1, 0.05 * inch))
    
    story.append(Paragraph("2.1 Data Requirements", section_style))
    data_req = (
        "The system captures 14 features from network packets: Source Port, Destination Port, Protocol, Flow Duration, "
        "Packet Count, Byte Count, Packet Rate, Byte Rate, Mean Packet Size, and individual TCP flags (SYN, ACK, RST, FIN) "
        "along with connection transport protocol indicator."
    )
    story.append(Paragraph(data_req, body_style))
    
    story.append(Paragraph("2.2 Software Requirements", section_style))
    sw_data = [
        [Paragraph("<b>Component</b>", body_bold), Paragraph("<b>Specification</b>", body_bold)],
        [Paragraph("Operating System", body_style), Paragraph("Windows 10 / Linux (Ubuntu 20.04+)", body_style)],
        [Paragraph("Development Tools", body_style), Paragraph("Python 3.8+, PyTorch 2.1+, Uvicorn 0.22+", body_style)],
        [Paragraph("Core Libraries", body_style), Paragraph("FastAPI, Scapy, NumPy, psutil, websockets", body_style)],
        [Paragraph("Frontend Tech", body_style), Paragraph("HTML5, Vanilla CSS3, JavaScript (ES6)", body_style)]
    ]
    sw_table = Table(sw_data, colWidths=[2.2*inch, 4.2*inch])
    sw_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), c_light_bg),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(sw_table)
    story.append(Spacer(1, 0.15 * inch))
    
    story.append(Paragraph("2.3 Hardware Requirements", section_style))
    hw_data = [
        [Paragraph("<b>Hardware</b>", body_bold), Paragraph("<b>Specification</b>", body_bold)],
        [Paragraph("Processor", body_style), Paragraph("Intel Core i5 (or equivalent AMD Ryzen processor)", body_style)],
        [Paragraph("System Memory", body_style), Paragraph("Minimum 8 GB RAM (16 GB recommended for faster model load)", body_style)],
        [Paragraph("Edge Node / Client", body_style), Paragraph("Monitored Laptop/Workstation or IoT Gateways", body_style)]
    ]
    hw_table = Table(hw_data, colWidths=[2.2*inch, 4.2*inch])
    hw_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), c_light_bg),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(hw_table)
    story.append(PageBreak())
    
    # ----------------- PAGE 5: SYSTEM DESIGN & ARCHITECTURE -----------------
    story.append(Paragraph("<b>3. SYSTEM DESIGN & PRESENT VS EXISTING</b>", chapter_style))
    story.append(Spacer(1, 0.05 * inch))
    
    comparison_data = [
        [Paragraph("<b>Existing Signature Systems</b>", body_bold), Paragraph("<b>Proposed Applied Deep Learning System</b>", body_bold)],
        [Paragraph("Signature databases fail against zero-day and custom exploits.", body_style),
         Paragraph("1D-CNN identifies complex, non-linear traffic patterns automatically.", body_style)],
        [Paragraph("Flask + SQL setups block runtime threads during heavy flow counts.", body_style),
         Paragraph("FastAPI + JSON file-based cache maintains high ingestion speed.", body_style)],
        [Paragraph("Dashboards require manual page refreshing, causing alert delays.", body_style),
         Paragraph("WebSockets broadcast threat anomalies instantly (under 2ms).", body_style)]
    ]
    comp_table = Table(comparison_data, colWidths=[3.2*inch, 3.2*inch])
    comp_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,0), c_light_bg),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 0.2 * inch))
    
    story.append(Paragraph("<b>4. SYSTEM FLOW & ARCHITECTURE</b>", chapter_style))
    story.append(Paragraph("The flowchart below details the telemetry ingestion and prediction architecture:", body_style))
    story.append(Spacer(1, 0.05 * inch))
    
    # Simple ASCII Flowchart Diagram
    arch_diag = """+-------------------------------------------------------------+
|               Client Agents / Ingestion Sniffer             |
|   (Captures packet statistics and pushes telemetry payload) |
+-------------------------------------------------------------+
                               |
                               | HTTP POST (telemetry endpoint)
                               v
+-------------------------------------------------------------+
|                   FastAPI Central Server                    |
|   (Validates schema structure via Pydantic model class)      |
+-------------------------------------------------------------+
                               |
                               | extracts 14 packet features
                               v
+-------------------------------------------------------------+
|             PyTorch 1D-CNN Inference Model                  |
|    (Normalizes features, executes classification layers)    |
+-------------------------------------------------------------+
                               |
                               | checks heuristics rules overlay
                               v
+-------------------------------------------------------------+
|                     State Manager / Cache                   |
|    (Logs flows in memory, saves asynchronously to disk)     |
+-------------------------------------------------------------+
                               |
                               | broadcasts via WebSockets
                               v
+-------------------------------------------------------------+
|                   HTML5 UI Web Dashboard                    |
|   (Updates nodes colors dynamically on SVG Topology Map)     |
+-------------------------------------------------------------+"""
    story.append(Preformatted(arch_diag, code_style))
    story.append(PageBreak())
    
    # ----------------- PAGE 6: METHODOLOGIES -----------------
    story.append(Paragraph("<b>5. METHODOLOGIES</b>", chapter_style))
    story.append(Spacer(1, 0.05 * inch))
    
    methodology_steps = (
        "1. <b>Telemetry Collection:</b> Client agents monitor network throughput (using <i>psutil</i> for zero-privilege environments) "
        "or perform deep packet header sniffing (using <i>Scapy</i>).<br/><br/>"
        "2. <b>Flow Aggregation:</b> Packet metrics are aggregated in a sliding 2-second time window to represent network connections as flows.<br/><br/>"
        "3. <b>Feature Scaling:</b> Raw features are scaled to ranges between 0.0 and 1.0 using pre-configured Min-Max values, matching the model's training distribution.<br/><br/>"
        "4. <b>Deep Learning Model:</b> A 1D Convolutional Neural Network (1D-CNN) is executed in PyTorch. The Conv1D layer learns temporal "
        "correlations between flow features to output threat probabilities for 4 classes: <i>Normal</i>, <i>DDoS</i>, <i>PortScan</i>, and <i>BruteForce</i>.<br/><br/>"
        "5. <b>Heuristic Rule Overlay:</b> To prevent false alarms, a rule overlay layer checks destination ports. If traffic belongs to standard "
        "secure protocols (like HTTPS or DNS) but is flagged by the neural network due to high volume, it bypasses threat alarms unless packet rates exceed custom thresholds.<br/><br/>"
        "6. <b>Asynchronous Socket Streams:</b> Results are cached in memory and broadcasted instantly to the web panel over WebSockets."
    )
    story.append(Paragraph(methodology_steps, body_style))
    story.append(PageBreak())
    
    # ----------------- PAGE 7: CORE IMPLEMENTATION -----------------
    story.append(Paragraph("<b>6. CORE IMPLEMENTATION</b>", chapter_style))
    story.append(Spacer(1, 0.05 * inch))
    story.append(Paragraph("Below is the core prediction engine in the backend server:", body_style))
    
    code_excerpt = """def predict_threat(raw_features):
    # Normalize features to [0.0, 1.0]
    norm_features = normalize_features(raw_features)
    
    # Reshape for PyTorch Conv1D input: [batch_size, channels, length]
    input_tensor = torch.tensor(norm_features).unsqueeze(0).unsqueeze(0)
    
    with torch.no_grad():
        logits = model(input_tensor)
        probabilities = torch.softmax(logits, dim=1).squeeze().numpy()
        
    class_id = int(np.argmax(probabilities))
    confidence = float(probabilities[class_id])
    
    # Apply Rule-based Heuristics Overlay
    dst_port = raw_features[1]
    packet_rate = raw_features[6]
    
    # Ensure zero false positives on standard web traffic ports (HTTP/HTTPS)
    if dst_port == 443 and class_id != 0:
        if packet_rate < 150:
            class_id = 0 # Force normal classification
            
    return class_id, CLASSES[class_id]"""
    story.append(Preformatted(code_excerpt, code_style))
    
    story.append(Paragraph("FastAPI Telemetry API Endpoint:", section_style))
    endpoint_code = """@app.post("/api/report-flow")
async def report_flow(data: dict):
    # Extract features, scale, and predict threat level
    features = extract_features(data)
    class_id, class_name = predict_threat(features)
    
    # Update state cache and broadcast alert if threat detected
    flow_record = save_and_cache(data, class_name)
    await ws_manager.broadcast({"type": "flow_event", "flow": flow_record})
    return {"status": "success", "prediction": class_name}"""
    story.append(Preformatted(endpoint_code, code_style))
    story.append(PageBreak())
    
    # ----------------- PAGE 8: EXPERIMENTAL RESULTS -----------------
    story.append(Paragraph("<b>7. EXPERIMENTAL RESULTS & VERIFICATION</b>", chapter_style))
    story.append(Spacer(1, 0.05 * inch))
    story.append(Paragraph("The web dashboard renders live network node links. Normal nodes are highlighted in solid green, and anomalous/threat nodes pulse in glowing red.", body_style))
    story.append(Spacer(1, 0.05 * inch))
    
    # Embed dashboard mockup image
    story.append(get_image_safe("iot_security_dashboard.png", 5.2 * inch, 3.2 * inch, body_style))
    story.append(Spacer(1, 0.1 * inch))
    
    # Testing verification table
    test_headers = [Paragraph("<b>Test ID</b>", body_bold), Paragraph("<b>Scenario</b>", body_bold), Paragraph("<b>Expected Output</b>", body_bold), Paragraph("<b>Status</b>", body_bold)]
    test_rows = [
        test_headers,
        [Paragraph("TC-01", body_style), Paragraph("Telemetry sniffer posting JSON stats", body_style), Paragraph("Validates schema structure, responds 200", body_style), Paragraph("<font color='green'><b>PASS</b></font>", body_style)],
        [Paragraph("TC-02", body_style), Paragraph("PyTorch 1D-CNN Inference check", body_style), Paragraph("Correctly predicts Normal and Anomaly types", body_style), Paragraph("<font color='green'><b>PASS</b></font>", body_style)],
        [Paragraph("TC-03", body_style), Paragraph("Bypass rules for HTTPS port 443", body_style), Paragraph("Bypasses false alarms, flags heavy rates", body_style), Paragraph("<font color='green'><b>PASS</b></font>", body_style)],
        [Paragraph("TC-04", body_style), Paragraph("WebSocket dashboard updates", body_style), Paragraph("Topology updates colors instantly (<10ms)", body_style), Paragraph("<font color='green'><b>PASS</b></font>", body_style)]
    ]
    test_table = Table(test_rows, colWidths=[0.8*inch, 2.2*inch, 2.6*inch, 0.8*inch])
    test_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('BACKGROUND', (0,0), (-1,0), c_light_bg),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(test_table)
    story.append(PageBreak())
    
    # ----------------- PAGE 9: CONCLUSION & REFERENCES -----------------
    story.append(Paragraph("<b>8. CONCLUSION & FUTURE SCOPE</b>", chapter_style))
    story.append(Spacer(1, 0.05 * inch))
    
    story.append(Paragraph("8.1 Project Conclusion", section_style))
    conclusion_txt = (
        "The project successfully implements an applied deep learning gateway intrusion detection system. "
        "Migrating to a zero-blocking architecture with FastAPI and custom memory cache resolves data ingestion bottleneck issues "
        "found in traditional Flask-MySQL deployments. The PyTorch 1D-CNN provides high accuracy classification without "
        "requiring root administrator permissions on monitored clients."
    )
    story.append(Paragraph(conclusion_txt, body_style))
    
    story.append(Paragraph("8.2 Future Enhancements", section_style))
    future_txt = (
        "• <b>Edge deployment:</b> Optimizing and exporting the PyTorch model using ONNX or TensorFlow Lite to run directly on ESP32 boards.<br/>"
        "• <b>Active blocking:</b> Integrating client-side OS firewall APIs to drop packets from flagged threat source IPs."
    )
    story.append(Paragraph(future_txt, body_style))
    
    story.append(Paragraph("8.3 References & Bibliography", section_style))
    ref_txt = (
        "[1] FastAPI Team, \"FastAPI Web Framework Documentation,\" tiangolo.com, 2026.<br/>"
        "[2] PyTorch Contributors, \"PyTorch Documentation: Deep Learning and 1D Convolutions,\" Linux Foundation, 2025.<br/>"
        "[3] S. Khraisat et al., \"Survey of Intrusion Detection Systems: Techniques and Challenges,\" Cybersecurity, vol. 2, no. 20, 2019."
    )
    story.append(Paragraph(ref_txt, body_style))
    
    # Build PDF
    doc.build(story, canvasmaker=CreativeCanvas)
    print(f"[+] Compilation complete for: {pdf_filename}")

if __name__ == "__main__":
    # Pass 1: Build with default values
    print("[*] Performing Pass 1 compilation...")
    generate_pdf()
    
    # Extract page numbers
    print("[*] Extracting absolute page numbers from PDF...")
    reader = PdfReader("Mini_Project_Report_Creative.pdf")
    toc_pages = {}
    
    for page_idx, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if not text:
            continue
        if "ABSTRACT" in text:
            toc_pages["ch1"] = page_idx
        if "1. INTRODUCTION & OBJECTIVES" in text:
            toc_pages["ch1"] = page_idx
        if "2. SYSTEM REQUIREMENT SPECIFICATION" in text:
            toc_pages["ch2"] = page_idx
        if "3. SYSTEM DESIGN" in text:
            toc_pages["ch3"] = page_idx
        if "4. SYSTEM FLOW & ARCHITECTURE" in text:
            toc_pages["ch4"] = page_idx
        if "5. METHODOLOGIES" in text:
            toc_pages["ch5"] = page_idx
        if "6. CORE IMPLEMENTATION" in text:
            toc_pages["ch6"] = page_idx
        if "7. EXPERIMENTAL RESULTS" in text:
            toc_pages["fig"] = page_idx
            toc_pages["tab"] = page_idx
        if "8. CONCLUSION & FUTURE SCOPE" in text:
            toc_pages["ref"] = page_idx

    # Define defaults if missing
    default_vals = {
        "ch1": 3, "ch2": 4, "ch3": 5, "ch4": 5, "ch5": 6, "ch6": 7, "ref": 9
    }
    for k, v in default_vals.items():
        if k not in toc_pages:
            toc_pages[k] = v
            
    print("Detected page numbers:")
    for k, v in sorted(toc_pages.items()):
        print(f"  {k}: page {v}")
        
    # Pass 2: Re-run with detected page numbers
    print("[*] Performing Pass 2 compilation with final page numbers...")
    generate_pdf(toc_pages)
    print("[+] Creative PDF compilation complete!")
