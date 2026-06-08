import java.util.*;
public class CollegePortal {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        ArrayList<Students> studentList = new ArrayList<>();
        ArrayList<Faculty> facultyList = new ArrayList<>();
        int choice = 0;
        do {
            System.out.println("\n--- College Portal Menu ---");
            System.out.println("1. Add Student");
            System.out.println("2. Add Faculty");
            System.out.println("3. View All Students");
            System.out.println("4. View All Faculty");
            System.out.println("5. Exit");
            System.out.print("Enter your choice: ");
            if (sc.hasNextInt()) {
                choice = sc.nextInt();
            } else {
                System.out.println("Invalid input. Please enter a number.");
                sc.next(); 
                continue; 
            }
            sc.nextLine(); 
            switch (choice) {
                case 1:
                    System.out.println("\n--- Enter Student Details ---");
                    Students student = new Students("", 0, "", "");
                    student.getDetails();
                    studentList.add(student);
                    System.out.println("Student added successfully!");
                    break;
                case 2:
                    System.out.println("\n--- Enter Faculty Details ---");
                    Faculty faculty = new Faculty("", "", "");
                    faculty.getDetails();
                    facultyList.add(faculty);
                    System.out.println("Faculty added successfully!");
                    break;
                case 3:
                    System.out.println("\n--- All Students ---");
                    if (studentList.isEmpty()) {
                        System.out.println("No students found. Please add a student first.");
                    }
                    for (Students s : studentList) {
                        s.displayDetails();
                    }
                    break;
                case 4:
                    System.out.println("\n--- All Faculty ---");
                    if (facultyList.isEmpty()) {
                        System.out.println("No faculty found. Please add a faculty member first.");
                    }
                    for (Faculty f : facultyList) {
                        f.displayDetails();
                    }
                    break;
                case 5:
                    System.out.println("Exiting the portal. Goodbye!");
                    break;
                default:
                    System.out.println("Invalid choice. Please select a valid option (1-5).");
            }
        } while (choice != 5);
        sc.close();
    }
}