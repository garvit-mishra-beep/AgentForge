"""
Acceptance Criteria Generator for AgentForge.
Generates acceptance criteria from user stories, requirements, or descriptions.
"""
import re
import json
from typing import List, Dict, Any, Optional
from .core import AcceptanceCriteria
import uuid


class AcceptanceCriteriaGenerator:
    """
    Generates acceptance criteria from various inputs like user stories,
    feature descriptions, or requirements documents.
    """

    def __init__(self):
        # Templates for different types of criteria
        self.templates = {
            "functional": [
                "Given {given}, when {when}, then {then}",
                "As a {role}, I want {goal} so that {benefit}",
                "The system shall {requirement}",
                "When {condition} occurs, the system shall {action}"
            ],
            "performance": [
                "Given {given}, when {when}, then the system shall respond within {time_limit}",
                "The system shall handle {load} requests per second with {response_time} response time",
                "Under {conditions}, the system throughput shall be at least {throughput}"
            ],
            "security": [
                "Given {given}, when {when}, then the system shall ensure {security_requirement}",
                "The system shall prevent {threat} by implementing {protection_mechanism}",
                "Access to {resource} shall be restricted to {authorized_roles}"
            ],
            "usability": [
                "Given {given}, when {when}, then the user shall be able to {action} within {time_limit}",
                "The interface shall be {usability_quality} for {user_type}",
                "Users shall complete {task} with no more than {max_steps} steps"
            ]
        }

        # Common patterns for extracting information from user stories
        self.user_story_pattern = re.compile(
            r"As a\s+(.*?),\s+I want\s+(.*?),\s+so that\s+(.*?)\.",
            re.IGNORECASE | re.DOTALL
        )

    def generate_from_user_story(self, user_story: str,
                               criteria_type: str = "functional") -> List[AcceptanceCriteria]:
        """
        Generate acceptance criteria from a user story.

        Args:
            user_story: The user story in "As a... I want... So that..." format
            criteria_type: Type of criteria to generate (functional, performance, security, usability)

        Returns:
            List of generated acceptance criteria
        """
        criteria_list = []

        # Try to parse as a standard user story
        match = self.user_story_pattern.search(user_story)
        if match:
            role, want, benefit = match.groups()
            role = role.strip()
            want = want.strip()
            benefit = benefit.strip()

            # Generate criteria based on the "I want" part
            base_criteria = AcceptanceCriteria(
                id=str(uuid.uuid4()),
                description=f"Verify that {want}",
                given=f"As a {role}",
                when=f"I attempt to {want}",
                then=f"I should achieve {benefit}",
                priority="high",
                category=criteria_type,
                metadata={
                    "source": "user_story",
                    "role": role,
                    "want": want,
                    "benefit": benefit
                }
            )
            criteria_list.append(base_criteria)

            # Add additional criteria based on type
            if criteria_type == "functional":
                criteria_list.extend(self._generate_functional_criteria(role, want, benefit))
            elif criteria_type == "performance":
                criteria_list.extend(self._generate_performance_criteria(role, want, benefit))
            elif criteria_type == "security":
                criteria_list.extend(self._generate_security_criteria(role, want, benefit))
            elif criteria_type == "usability":
                criteria_list.extend(self._generate_usability_criteria(role, want, benefit))

        else:
            # Fallback: treat as general requirement
            criteria = AcceptanceCriteria(
                id=str(uuid.uuid4()),
                description=user_story[:100] + ("..." if len(user_story) > 100 else ""),
                given="The system is operational",
                when=f"The user interacts with the system to {user_story.lower()}",
                then="The system behaves as expected",
                priority="medium",
                category=criteria_type,
                metadata={"source": "requirement", "raw_input": user_story}
            )
            criteria_list.append(criteria)

        return criteria_list

    def generate_from_description(self, description: str,
                                context: str = "",
                                criteria_type: str = "functional") -> List[AcceptanceCriteria]:
        """
        Generate acceptance criteria from a feature description.

        Args:
            description: Description of the feature or requirement
            context: Additional context about the feature
            criteria_type: Type of criteria to generate

        Returns:
            List of generated acceptance criteria
        """
        criteria_list = []

        # Extract key actions/features from the description
        actions = self._extract_actions(description)

        for i, action in enumerate(actions):
            criteria = AcceptanceCriteria(
                id=str(uuid.uuid4()),
                description=f"Verify {action}",
                given=context if context else "The system is ready",
                when=f"The user attempts to {action}",
                then=f"The system successfully completes {action}",
                priority="high" if i == 0 else "medium",  # First action is usually primary
                category=criteria_type,
                metadata={
                    "source": "description",
                    "action_index": i,
                    "total_actions": len(actions)
                }
            )
            criteria_list.append(criteria)

        # If no actions found, create a generic criterion
        if not actions:
            criteria = AcceptanceCriteria(
                id=str(uuid.uuid4()),
                description=description[:100] + ("..." if len(description) > 100 else ""),
                given=context if context else "Preconditions are met",
                when="The feature is exercised",
                then="The expected outcome is observed",
                priority="medium",
                category=criteria_type,
                metadata={"source": "description", "raw_input": description}
            )
            criteria_list.append(criteria)

        return criteria_list

    def _extract_actions(self, text: str) -> List[str]:
        """Extract action verbs and phrases from text."""
        # Simple implementation: look for verb phrases
        action_patterns = [
            r'\b(can|should|must|will|shall)\s+([^,\.]+)',
            r'\b(to\s+[^,\.]+)',
            r'\b([a-z]+ing\s+[^,\.]+)'
        ]

        actions = []
        for pattern in action_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    action = ' '.join(mask for mask in match if mask).strip()
                else:
                    action = match.strip()
                if action and len(action) > 3:  # Filter out too short matches
                    actions.append(action)

        # Also look for imperative sentences
        imperative_matches = re.findall(
            r'^\s*([a-z]+(?:\s+[a-z]+)*\s+[^,\.]+)',
            text,
            re.IGNORECASE | re.MULTILINE
        )
        actions.extend([match.strip() for match in imperative_matches if len(match.strip()) > 3])

        # Remove duplicates while preserving order
        seen = set()
        unique_actions = []
        for action in actions:
            if action.lower() not in seen:
                seen.add(action.lower())
                unique_actions.append(action)

        return unique_actions[:5]  # Limit to top 5 actions

    def _generate_functional_criteria(self, role: str, want: str, benefit: str) -> List[AcceptanceCriteria]:
        """Generate additional functional criteria."""
        criteria = []

        # Error handling criteria
        criteria.append(AcceptanceCriteria(
            id=str(uuid.uuid4()),
            description=f"Handle invalid inputs when trying to {want}",
            given=f"As a {role} with invalid or unexpected input",
            when=f"I attempt to {want}",
            then="The system provides clear error messages and does not crash",
            priority="high",
            category="functional",
            metadata={"source": "generated", "type": "error_handling"}
        ))

        # Boundary conditions
        criteria.append(AcceptanceCriteria(
            id=str(uuid.uuid4()),
            description=f"Handle boundary conditions when trying to {want}",
            given=f"As a {role} with boundary value inputs",
            when=f"I attempt to {want}",
            then="The system behaves correctly at boundaries",
            priority="medium",
            category="functional",
            metadata={"source": "generated", "type": "boundary"}
        ))

        return criteria

    def _generate_performance_criteria(self, role: str, want: str, benefit: str) -> List[AcceptanceCriteria]:
        """Generate performance-related criteria."""
        criteria = []

        criteria.append(AcceptanceCriteria(
            id=str(uuid.uuid4()),
            description=f"System responds within acceptable time when trying to {want}",
            given=f"As a {role} under normal load conditions",
            when=f"I perform {want}",
            then="The system responds within 2 seconds (adjust based on requirements)",
            priority="high",
            category="performance",
            metadata={"source": "generated", "type": "response_time"}
        ))

        return criteria

    def _generate_security_criteria(self, role: str, want: str, benefit: str) -> List[AcceptanceCriteria]:
        """Generate security-related criteria."""
        criteria = []

        criteria.append(AcceptanceCriteria(
            id=str(uuid.uuid4()),
            description=f"Unauthorized users cannot perform {want}",
            given=f"As an unauthenticated or unauthorized user",
            when=f"I attempt to {want}",
            then="The system denies access and logs the attempt",
            priority="high",
            category="security",
            metadata={"source": "generated", "type": "access_control"}
        ))

        return criteria

    def _generate_usability_criteria(self, role: str, want: str, benefit: str) -> List[AcceptanceCriteria]:
        """Generate usability-related criteria."""
        criteria = []

        criteria.append(AcceptanceCriteria(
            id=str(uuid.uuid4()),
            description=f"Task {want} is intuitive for {role}",
            given=f"As a {role} unfamiliar with this feature",
            when=f"I attempt to {want} for the first time",
            then="I can complete the task without external help",
            priority="medium",
            category="usability",
            metadata={"source": "generated", "type": "learnability"}
        ))

        return criteria

    def bulk_generate(self, requirements: List[Dict[str, Any]]) -> List[AcceptanceCriteria]:
        """
        Generate acceptance criteria for multiple requirements.

        Args:
            requirements: List of requirement dictionaries with keys:
                         - description: The requirement text
                         - type: Optional type (functional, performance, etc.)
                         - context: Optional context
                         - user_story: Optional user story format

        Returns:
            List of all generated acceptance criteria
        """
        all_criteria = []

        for req in requirements:
            if "user_story" in req and req["user_story"]:
                criteria = self.generate_from_user_story(
                    req["user_story"],
                    req.get("type", "functional")
                )
            else:
                criteria = self.generate_from_description(
                    req["description"],
                    req.get("context", ""),
                    req.get("type", "functional")
                )
            all_criteria.extend(criteria)

        return all_criteria

    def to_json(self, criteria_list: List[AcceptanceCriteria]) -> str:
        """Convert criteria list to JSON string."""
        return json.dumps([self._criteria_to_dict(c) for c in criteria_list], indent=2)

    def from_json(self, json_str: str) -> List[AcceptanceCriteria]:
        """Create criteria list from JSON string."""
        data = json.loads(json_str)
        return [self._dict_to_criteria(item) for item in data]

    def _criteria_to_dict(self, criteria: AcceptanceCriteria) -> Dict[str, Any]:
        """Convert AcceptanceCriteria to dictionary."""
        return {
            "id": criteria.id,
            "description": criteria.description,
            "given": criteria.given,
            "when": criteria.when,
            "then": criteria.then,
            "priority": criteria.priority,
            "category": criteria.category,
            "testable": criteria.testable,
            "metadata": criteria.metadata
        }

    def _dict_to_criteria(self, data: Dict[str, Any]) -> AcceptanceCriteria:
        """Convert dictionary to AcceptanceCriteria."""
        return AcceptanceCriteria(
            id=data["id"],
            description=data["description"],
            given=data["given"],
            when=data["when"],
            then=data["then"],
            priority=data.get("priority", "medium"),
            category=data.get("category", "functional"),
            testable=data.get("testable", True),
            metadata=data.get("metadata", {})
        )
