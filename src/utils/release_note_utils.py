def generate_release_note_text(release_name, repository, tag, deployment_status, jira_issues, commits=None):
    note = []
    note.append(f"# Release: {release_name or 'N/A'}")
    note.append(f"Repository: {repository or 'N/A'}")
    note.append(f"Tag: {tag or 'N/A'}")
    note.append(f"Deployment Status: {deployment_status or 'N/A'}")
    note.append("\n---\n")
    note.append("## Enriched Jira Issues\n")
    if not jira_issues:
        note.append("No Jira issues enriched.\n")
    else:
        for issue in jira_issues:
            if isinstance(issue, dict):
                note.append(f"- **{issue.get('key', '')}: {issue.get('summary', '')}**")
                note.append(f"  - Executive Summary: {issue.get('executive_summary', '')}")
                note.append(f"  - Technical Summary: {issue.get('technical_summary', '')}")
                note.append(f"  - Root Cause: {issue.get('root_cause', '')}")
                note.append(f"  - Fix: {issue.get('fix', '')}")
                note.append(f"  - Impact: {issue.get('impact', '')}\n")
            else:
                # Print error string or unknown object
                note.append(f"- [ERROR] {str(issue)}\n")
    if commits:
        note.append("## Related Commits")
        for commit in commits:
            note.append(f"- {commit}")
    return "\n".join(note)