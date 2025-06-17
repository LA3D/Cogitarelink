"""cogitarelink: Research agent entry point for Claude Code integration.

Prints semantic research methodology instructions directly to Claude Code context.
Follows Claude Code's instruction-driven enhancement pattern.
"""

from ..prompts.instruction_generator import generate_general_research_instructions


# CLI Command - Direct Instruction Printing (Claude Code Pattern)

def main():
    """CogitareLink: Print semantic research instructions to Claude Code context.
    
    Follows Claude Code's instruction-driven enhancement pattern.
    No CLI subcommands - just prints methodology directly.
    """
    # Print general research methodology instructions directly
    instructions = generate_general_research_instructions()
    print(instructions)


if __name__ == "__main__":
    main()