import streamlit as st
import os
import tempfile
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import PyPDF2
import docx
import re

# Set up the page configuration
st.set_page_config(layout="wide", page_title="Multi-Agent RFP Response System")

# --- Introduction and API Key Configuration ---
st.title("Multi-Agent RFP Winning Response System 🤖")
st.markdown("This application helps you create winning RFP responses using multiple AI agents. Follow the tabs to progress through the RFP analysis and response generation.")

# Get OpenAI API Key from user
with st.sidebar:
    st.header("1. Configuration")
    api_key = st.text_input("Enter your OpenAI API Key", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("API key set successfully!")
    else:
        st.warning("Please enter your OpenAI API key to proceed.")

# --- Session State Initialization ---
if 'page' not in st.session_state:
    st.session_state.page = "Agent 1 - Company Details"
if 'company_details' not in st.session_state:
    st.session_state.company_details = {}
if 'rfp_content' not in st.session_state:
    st.session_state.rfp_content = ""
if 'scope_analysis' not in st.session_state:
    st.session_state.scope_analysis = {}
if 'winning_proposal' not in st.session_state:
    st.session_state.winning_proposal = ""
if 'competitors' not in st.session_state:
    st.session_state.competitors = [""]
if 'company_info_extracted' not in st.session_state:
    st.session_state.company_info_extracted = False

# --- Agent and LLM Setup ---
def create_agent(system_prompt):
    """
    Creates a simple LLM agent using the specified system prompt.
    """
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OpenAI API key is not set. Please configure it in the sidebar.")
        return None
    
    llm = ChatOpenAI(model="gpt-4o-mini")
    messages = [SystemMessage(content=system_prompt)]
    return llm, messages

def run_agent(llm, messages, user_content):
    """
    Runs the agent with the user's content and returns the response.
    """
    messages.append(HumanMessage(content=user_content))
    try:
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        st.error(f"Error calling the LLM: {e}")
        return None

def extract_text_from_pdf(uploaded_file):
    """Extract text from PDF file"""
    try:
        # Use pypdf (recommended - it's the maintained version)
        import pypdf
        pdf_reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def extract_text_from_docx(uploaded_file):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(uploaded_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
        return ""

def extract_company_details(company_info_text):
    """
    Uses AI to automatically extract and structure company details from provided information
    """
    system_prompt = """You are an expert business analyst specializing in company profiling and competitive intelligence. 
    Your task is to analyze the provided company information and extract structured details including:
    
    1. COMPANY STRENGTHS & CAPABILITIES:
       - Technical expertise and specializations
       - Key personnel strengths
       - Infrastructure capabilities
       - Process methodologies
       - Quality assurance practices
    
    2. CASE STUDIES & REFERENCES:
       - Successful project examples
       - Client testimonials and results
       - Industry-specific experience
       - Performance metrics and achievements
    
    3. UNIQUE SELLING POINTS (USPs):
       - Competitive differentiators
       - Innovative approaches
       - Unique methodologies
       - Special certifications or awards
       - Proprietary technologies
    
    4. INDUSTRY EXPERTISE:
       - Specific industry verticals
       - Domain knowledge
       - Regulatory compliance expertise
       - Market recognition
    
    Format your response in clear, structured sections that can be directly used in RFP responses.
    Focus on quantifiable achievements and specific capabilities that would be compelling in a proposal."""
    
    llm, messages = create_agent(system_prompt)
    if llm:
        extracted_details = run_agent(llm, messages, company_info_text)
        return extracted_details
    return None

def analyze_company_documents(uploaded_files):
    """
    Analyzes multiple company documents to extract comprehensive company information
    """
    combined_text = ""
    
    for uploaded_file in uploaded_files:
        if uploaded_file.type == "application/pdf":
            combined_text += extract_text_from_pdf(uploaded_file) + "\n\n"
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            combined_text += extract_text_from_docx(uploaded_file) + "\n\n"
        else:
            combined_text += uploaded_file.getvalue().decode("utf-8") + "\n\n"
    
    if combined_text:
        return extract_company_details(combined_text)
    return None

# --- Main App Tabs/Navigation ---
page = st.sidebar.radio(
    "2. Navigation",
    [
        "Agent 1 - Company Details",
        "Agent 2 - RFP Scope Analysis",
        "Agent 3 - Winning Proposal Generation",
        "Final Proposal"
    ],
    index=["Agent 1 - Company Details", "Agent 2 - RFP Scope Analysis", "Agent 3 - Winning Proposal Generation", "Final Proposal"].index(st.session_state.page)
)
st.session_state.page = page

# --- Content for Each Tab ---

# Tab 1: Agent 1 - Company Details
if page == "Agent 1 - Company Details":
    st.header("Agent 1: Company & Competitor Information")
    st.markdown("Please provide your company details and upload the RFP document.")
    
    # Company details input methods
    st.subheader("Company Information Input Methods")
    
    input_method = st.radio(
        "Choose how to provide company information:",
        ["Manual Entry", "Upload Company Documents", "Paste Company Information"],
        horizontal=True
    )
    
    company_info_text = ""
    
    if input_method == "Manual Entry":
        st.subheader("Your Company Information")
        st.session_state.company_details["company_name"] = st.text_input("Your Company Name", value=st.session_state.company_details.get("company_name", ""))
        st.session_state.company_details["industry_focus"] = st.text_input("Industry Focus", value=st.session_state.company_details.get("industry_focus", ""))
        st.session_state.company_details["key_strengths"] = st.text_area("Key Strengths/Capabilities", value=st.session_state.company_details.get("key_strengths", ""), 
                                                                        placeholder="Describe your technical expertise, team capabilities, infrastructure, methodologies...")
        st.session_state.company_details["past_case_studies"] = st.text_area("Past Case Studies/References", value=st.session_state.company_details.get("past_case_studies", ""),
                                                                            placeholder="Include successful projects, client testimonials, measurable results, performance metrics...")
        st.session_state.company_details["unique_selling_points"] = st.text_area("Unique Selling Points", value=st.session_state.company_details.get("unique_selling_points", ""),
                                                                                placeholder="What makes you different from competitors? Innovative approaches, proprietary technology, special certifications...")
        
        # Combine manual entries for extraction
        if st.session_state.company_details["company_name"]:
            company_info_text = f"""
            Company: {st.session_state.company_details["company_name"]}
            Industry Focus: {st.session_state.company_details["industry_focus"]}
            Key Strengths: {st.session_state.company_details["key_strengths"]}
            Case Studies: {st.session_state.company_details["past_case_studies"]}
            Unique Selling Points: {st.session_state.company_details["unique_selling_points"]}
            """
    
    elif input_method == "Upload Company Documents":
        st.subheader("Upload Company Documents")
        st.markdown("Upload any company documents that contain information about your capabilities, case studies, strengths, or unique selling points.")
        
        uploaded_company_files = st.file_uploader(
            "Upload Company Documents (PDF, DOCX, TXT)", 
            type=["pdf", "docx", "txt"], 
            accept_multiple_files=True,
            key="company_docs"
        )
        
        if uploaded_company_files:
            st.success(f"Uploaded {len(uploaded_company_files)} company document(s)")
            
            # Show preview of uploaded files
            with st.expander("Uploaded Documents Preview"):
                for i, doc in enumerate(uploaded_company_files):
                    st.write(f"**Document {i+1}: {doc.name}**")
                    if doc.type == "text/plain":
                        content = doc.getvalue().decode("utf-8")
                        st.text(content[:500] + "..." if len(content) > 500 else content)
            
            if st.button("Extract Company Details from Documents"):
                with st.spinner("Analyzing company documents to extract key details..."):
                    extracted_info = analyze_company_documents(uploaded_company_files)
                    if extracted_info:
                        st.session_state.company_info_extracted = True
                        st.session_state.extracted_company_details = extracted_info
                        st.success("Company details extracted successfully!")
                        
                        # Display extracted information
                        st.subheader("Extracted Company Details")
                        st.text_area("AI-Extracted Company Profile", extracted_info, height=400)
                        
                        # Option to use extracted details
                        if st.button("Use These Extracted Details"):
                            # Parse the extracted information back into the form fields
                            lines = extracted_info.split('\n')
                            current_section = ""
                            
                            for line in lines:
                                if "STRENGTHS" in line.upper() or "CAPABILITIES" in line.upper():
                                    current_section = "strengths"
                                elif "CASE STUDIES" in line.upper() or "REFERENCES" in line.upper():
                                    current_section = "case_studies"
                                elif "UNIQUE SELLING" in line.upper() or "USP" in line.upper():
                                    current_section = "usps"
                                elif "INDUSTRY" in line.upper() or "EXPERTISE" in line.upper():
                                    current_section = "industry"
                                else:
                                    if current_section == "strengths":
                                        st.session_state.company_details["key_strengths"] += line + "\n"
                                    elif current_section == "case_studies":
                                        st.session_state.company_details["past_case_studies"] += line + "\n"
                                    elif current_section == "usps":
                                        st.session_state.company_details["unique_selling_points"] += line + "\n"
                                    elif current_section == "industry":
                                        st.session_state.company_details["industry_focus"] += line + "\n"
                            
                            st.success("Extracted details applied to form!")
                            st.rerun()
    
    elif input_method == "Paste Company Information":
        st.subheader("Paste Company Information")
        company_info_paste = st.text_area(
            "Paste all relevant company information here:",
            height=300,
            placeholder="Paste any text containing information about your company:\n- Company capabilities and strengths\n- Past projects and case studies\n- Client testimonials and results\n- Unique features and differentiators\n- Industry expertise and certifications\n- Team qualifications and experience\n- Technical infrastructure and methodologies\n- Awards and recognition"
        )
        
        if company_info_paste:
            company_info_text = company_info_paste
            
            if st.button("Extract and Structure Company Details"):
                with st.spinner("Analyzing company information to extract key details..."):
                    extracted_info = extract_company_details(company_info_paste)
                    if extracted_info:
                        st.session_state.company_info_extracted = True
                        st.session_state.extracted_company_details = extracted_info
                        st.success("Company details extracted successfully!")
                        
                        st.subheader("Extracted Company Details")
                        st.text_area("AI-Extracted Company Profile", extracted_info, height=400)
    
    # Auto-extraction button for manual entries
    if input_method == "Manual Entry" and company_info_text and st.button("Enhance Company Details with AI"):
        with st.spinner("Analyzing and enhancing company details..."):
            enhanced_details = extract_company_details(company_info_text)
            if enhanced_details:
                st.session_state.enhanced_company_details = enhanced_details
                st.success("Company details enhanced with AI!")
                
                st.subheader("AI-Enhanced Company Details")
                st.text_area("Enhanced Company Profile", enhanced_details, height=400)
    
    # Competitor information with dynamic addition
    st.subheader("Competitor Companies")
    st.markdown("Add competitor companies that are likely bidding for this RFP:")
    
    # Initialize competitors list if not exists
    if 'competitors' not in st.session_state:
        st.session_state.competitors = [""]
    
    # Display current competitors
    for i, competitor in enumerate(st.session_state.competitors):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.session_state.competitors[i] = st.text_input(
                f"Competitor {i+1}", 
                value=competitor,
                key=f"competitor_{i}"
            )
        with col2:
            if i > 0:  # Don't show remove button for first competitor
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.competitors.pop(i)
                    st.rerun()
    
    # Add new competitor button
    if st.button("➕ Add Competitor"):
        st.session_state.competitors.append("")
        st.rerun()
    
    # RFP Document Upload
    st.subheader("RFP Document Upload")
    uploaded_file = st.file_uploader("Upload RFP Document", type=["pdf", "docx", "txt"])
    
    if uploaded_file is not None:
        # Extract text based on file type
        if uploaded_file.type == "application/pdf":
            st.session_state.rfp_content = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            st.session_state.rfp_content = extract_text_from_docx(uploaded_file)
        else:
            st.session_state.rfp_content = uploaded_file.getvalue().decode("utf-8")
        
        st.success(f"RFP document uploaded successfully! Extracted {len(st.session_state.rfp_content)} characters.")
        
        # Show preview
        with st.expander("RFP Content Preview"):
            st.text_area("Preview", st.session_state.rfp_content[:2000] + "..." if len(st.session_state.rfp_content) > 2000 else st.session_state.rfp_content, height=300)

# Tab 2: Agent 2 - RFP Scope Analysis
elif page == "Agent 2 - RFP Scope Analysis":
    st.header("Agent 2: RFP Scope Analysis")
    
    if not st.session_state.rfp_content:
        st.warning("Please upload an RFP document in the 'Agent 1 - Company Details' tab first.")
    else:
        st.markdown("Agent 2 will analyze the RFP document and break down the complete scope.")
        
        if st.button("Analyze RFP Scope"):
            with st.spinner("Agent 2 is analyzing the RFP scope..."):
                system_prompt = """You are an expert RFP analyst. Your task is to thoroughly analyze RFP documents and break down the complete scope into structured categories. 
                You must identify and categorize all requirements, timelines, evaluation criteria, and submission instructions.
                
                Provide your analysis in the following structured format:
                
                FUNCTIONAL REQUIREMENTS:
                - List all functional requirements clearly
                - Group related requirements
                - Identify mandatory vs optional requirements
                
                NON-FUNCTIONAL REQUIREMENTS:
                - Performance requirements
                - Security requirements
                - Scalability requirements
                - Compliance requirements
                - Technical constraints
                
                PURPOSE & OBJECTIVES:
                - Main business objectives
                - Expected outcomes
                - Success criteria
                
                SCOPE SUMMARY:
                - Overall project scope
                - In-scope items
                - Out-of-scope items (if mentioned)
                - Deliverables
                
                TIMELINES & MILESTONES:
                - Key deadlines
                - Project timeline
                - Milestone dates
                - Submission deadlines
                
                SUBMISSION INSTRUCTIONS:
                - Format requirements
                - Required sections
                - Documentation needed
                - Submission process
                
                PROPOSAL EVALUATION CRITERIA:
                - Scoring methodology
                - Weightage of different sections
                - Key evaluation factors
                - Decision criteria"""
                
                llm, messages = create_agent(system_prompt)
                if llm:
                    analysis_result = run_agent(llm, messages, st.session_state.rfp_content)
                    st.session_state.scope_analysis = analysis_result
                    
        if st.session_state.scope_analysis:
            st.subheader("RFP Scope Analysis Results")
            st.text_area("Analysis Results", st.session_state.scope_analysis, height=600)
            
            # Download option
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as temp_file:
                temp_file.write(st.session_state.scope_analysis)
                temp_file_path = temp_file.name

            st.download_button(
                label="Download Scope Analysis",
                data=open(temp_file_path, "rb").read(),
                file_name="rfp_scope_analysis.txt",
                mime="text/plain"
            )

# Tab 3: Agent 3 - Winning Proposal Generation
elif page == "Agent 3 - Winning Proposal Generation":
    st.header("Agent 3: Winning Proposal Generation")
    
    if not st.session_state.scope_analysis or not st.session_state.company_details.get("company_name"):
        st.warning("Please complete both Agent 1 (Company Details) and Agent 2 (RFP Analysis) first.")
    else:
        st.markdown("Agent 3 will create a winning proposal by leveraging your company's strengths and addressing the RFP requirements.")
        
        # Additional inputs for proposal customization
        st.subheader("Proposal Customization")
        proposal_tone = st.selectbox(
            "Proposal Tone",
            ["Professional", "Innovative", "Confident", "Collaborative", "Technical"],
            help="Select the tone that best suits your company and the RFP requirements"
        )
        
        emphasis_areas = st.multiselect(
            "Key Areas to Emphasize",
            ["Technical Expertise", "Cost Effectiveness", "Innovation", "Experience", "Partnership Approach", "Speed of Delivery", "Quality Assurance"],
            default=["Technical Expertise", "Experience"],
            help="Select the areas where your company has the strongest advantages"
        )
        
        # Use extracted company details if available
        company_details_to_use = ""
        if hasattr(st.session_state, 'extracted_company_details') and st.session_state.company_info_extracted:
            company_details_to_use = st.session_state.extracted_company_details
        else:
            # Fall back to manual entries
            company_details_to_use = f"""
            Company Name: {st.session_state.company_details.get("company_name")}
            Industry Focus: {st.session_state.company_details.get("industry_focus")}
            Key Strengths: {st.session_state.company_details.get("key_strengths")}
            Unique Selling Points: {st.session_state.company_details.get("unique_selling_points")}
            Past Case Studies: {st.session_state.company_details.get("past_case_studies")}
            """
        
        if st.button("Generate Winning Proposal"):
            with st.spinner("Agent 3 is crafting your winning proposal..."):
                system_prompt = f"""You are a top-tier proposal writer specializing in creating winning RFP responses. Your task is to create a compelling, professional proposal that highlights the client's strengths and addresses all RFP requirements while differentiating from competitors.

                Guidelines:
                1. Create a comprehensive, well-structured proposal
                2. Emphasize {st.session_state.company_details.get("company_name")}'s strengths and relevant experience
                3. Address all functional and non-functional requirements from the RFP
                4. Use a {proposal_tone.lower()} tone throughout
                5. Highlight these key areas: {', '.join(emphasis_areas)}
                6. Incorporate case studies and references strategically
                7. Differentiate from competitors: {', '.join([c for c in st.session_state.competitors if c])}
                8. Structure the proposal to maximize evaluation scores

                Required Proposal Structure:
                - Executive Summary
                - Company Overview & Relevant Experience
                - Understanding of Requirements
                - Proposed Solution
                - Technical Approach
                - Project Timeline & Milestones
                - Team Composition
                - Case Studies & References
                - Pricing Strategy (if applicable)
                - Differentiators vs Competitors
                - Risk Management
                - Conclusion & Next Steps"""
                
                proposal_prompt = f"""
                COMPANY INFORMATION:
                {company_details_to_use}
                
                COMPETITORS: {', '.join([c for c in st.session_state.competitors if c])}
                
                RFP SCOPE ANALYSIS:
                {st.session_state.scope_analysis}
                
                Please create a comprehensive winning proposal that addresses all RFP requirements while highlighting our competitive advantages and relevant experience.
                """
                
                llm, messages = create_agent(system_prompt)
                if llm:
                    st.session_state.winning_proposal = run_agent(llm, messages, proposal_prompt)

        if st.session_state.winning_proposal:
            st.subheader("Generated Winning Proposal")
            st.text_area("Winning Proposal", st.session_state.winning_proposal, height=600)
            
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as temp_file:
                temp_file.write(st.session_state.winning_proposal)
                temp_file_path = temp_file.name

            st.download_button(
                label="Download Proposal",
                data=open(temp_file_path, "rb").read(),
                file_name="winning_proposal.txt",
                mime="text/plain"
            )

# Tab 4: Final Proposal
elif page == "Final Proposal":
    st.header("Final Winning Proposal")
    
    if not st.session_state.winning_proposal:
        st.warning("Please generate a proposal in the 'Agent 3 - Winning Proposal Generation' tab first.")
    else:
        st.markdown("### Your Complete RFP Response")
        
        # Display the final proposal
        st.text_area("Final Proposal", st.session_state.winning_proposal, height=600)
        
        # Additional refinement options
        st.subheader("Proposal Refinement")
        refinement_request = st.text_area(
            "Request specific refinements (optional):",
            placeholder="E.g., Make the executive summary more compelling, emphasize cost benefits, add more technical details..."
        )
        
        if st.button("Refine Proposal") and refinement_request:
            with st.spinner("Refining proposal..."):
                system_prompt = "You are an expert proposal editor. Refine the provided proposal based on the specific refinement requests while maintaining its professional quality and structure."
                llm, messages = create_agent(system_prompt)
                if llm:
                    refinement_prompt = f"""
                    ORIGINAL PROPOSAL:
                    {st.session_state.winning_proposal}
                    
                    REFINEMENT REQUEST:
                    {refinement_request}
                    
                    Please provide an improved version of the proposal that addresses the refinement request while keeping all the original strengths and structure.
                    """
                    refined_proposal = run_agent(llm, messages, refinement_prompt)
                    if refined_proposal:
                        st.session_state.winning_proposal = refined_proposal
                        st.success("Proposal refined successfully!")
                        st.rerun()
        
        # Final download options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as temp_file:
                temp_file.write(st.session_state.winning_proposal)
                temp_file_path = temp_file.name

            st.download_button(
                label="📄 Download as TXT",
                data=open(temp_file_path, "rb").read(),
                file_name="rfp_winning_proposal.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            # Create a simple formatted version
            formatted_content = f"""
            RFP WINNING PROPOSAL
            ====================
            
            Prepared for: {st.session_state.company_details.get("company_name", "Your Company")}
            
            {st.session_state.winning_proposal}
            """
            
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as temp_file:
                temp_file.write(formatted_content)
                temp_file_path = temp_file.name

            st.download_button(
                label="📝 Download as MD",
                data=open(temp_file_path, "rb").read(),
                file_name="rfp_winning_proposal.md",
                mime="text/plain",
                use_container_width=True
            )
        
        with col3:
            st.info("💡 **Next Steps:** Review the proposal, customize any company-specific details, and ensure all RFP requirements are addressed before submission.")

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.markdown("### System Status")
if st.session_state.rfp_content:
    st.sidebar.success("✅ RFP Document Uploaded")
if st.session_state.scope_analysis:
    st.sidebar.success("✅ RFP Analysis Complete")
if st.session_state.winning_proposal:
    st.sidebar.success("✅ Proposal Generated")
if st.session_state.company_info_extracted:
    st.sidebar.success("✅ Company Details Enhanced")

st.sidebar.markdown("""
### How it works:
1. **Agent 1**: Collects company info and RFP document
2. **Agent 2**: Analyzes RFP scope and requirements  
3. **Agent 3**: Creates winning proposal strategy
4. **Final**: Refines and delivers complete response
""")
