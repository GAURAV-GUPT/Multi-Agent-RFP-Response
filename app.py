import streamlit as st
import os
import tempfile
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import PyPDF2
import docx

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
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
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
    
    # Company details
    st.subheader("Your Company Information")
    st.session_state.company_details["company_name"] = st.text_input("Your Company Name", value=st.session_state.company_details.get("company_name", ""))
    st.session_state.company_details["industry_focus"] = st.text_input("Industry Focus", value=st.session_state.company_details.get("industry_focus", ""))
    st.session_state.company_details["key_strengths"] = st.text_area("Key Strengths/Capabilities", value=st.session_state.company_details.get("key_strengths", ""))
    st.session_state.company_details["past_case_studies"] = st.text_area("Past Case Studies/References", value=st.session_state.company_details.get("past_case_studies", ""))
    st.session_state.company_details["unique_selling_points"] = st.text_area("Unique Selling Points", value=st.session_state.company_details.get("unique_selling_points", ""))
    
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
                Company Name: {st.session_state.company_details.get("company_name")}
                Industry Focus: {st.session_state.company_details.get("industry_focus")}
                Key Strengths: {st.session_state.company_details.get("key_strengths")}
                Unique Selling Points: {st.session_state.company_details.get("unique_selling_points")}
                Past Case Studies: {st.session_state.company_details.get("past_case_studies")}
                
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

st.sidebar.markdown("""
### How it works:
1. **Agent 1**: Collects company info and RFP document
2. **Agent 2**: Analyzes RFP scope and requirements  
3. **Agent 3**: Creates winning proposal strategy
4. **Final**: Refines and delivers complete response
""")
