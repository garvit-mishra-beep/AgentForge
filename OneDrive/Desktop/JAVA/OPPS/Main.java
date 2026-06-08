import java.util.*;
class Students {
    String name;
    int age;
    String batch;
    String rollNo;
    Students(String stuname, int stuage, String stubatch, String sturollno) {
        name = stuname;
        age = stuage;
        batch = stubatch;
        rollNo = sturollno;
    }

    void getStudentDetails() {
        Scanner sc = new Scanner(System.in);
        System.out.print("Enter student name: ");
        name = sc.nextLine();
        System.out.print("Enter age: ");
        age = sc.nextInt();
        sc.nextLine();
        System.out.print("Enter batch: ");
        batch = sc.nextLine();
        System.out.print("Enter roll number: ");
        rollNo = sc.nextLine();
    }

    void displayStudentDetails() {
        System.out.println("\nStudent Details:");
        System.out.println("Name: " + name);
        System.out.println("Age: " + age);
        System.out.println("Batch: " + batch);
        System.out.println("Roll Number: " + rollNo);
    }
}
class Faculty {
    String name;
    String department;
    String employeeId;
    Faculty(String fname, String fdepartment, String femployeeId) {
        name = fname;
        department = fdepartment;
        employeeId = femployeeId;
    }
    void getFacultyDetails() {
        Scanner sc = new Scanner(System.in);
        System.out.print("Enter faculty name: ");
        name = sc.nextLine();
        System.out.print("Enter department: ");
        department = sc.nextLine();
        System.out.print("Enter employee ID: ");
        employeeId = sc.nextLine();
    }
    void displayFacultyDetails() {
        System.out.println("\nFaculty Details:");
        System.out.println("Name: " + name);
        System.out.println("Department: " + department);
        System.out.println("Employee ID: " + employeeId);
    }
}
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        System.out.println("1. Student");
        System.out.println("2. Faculty");
        System.out.print("Enter your choice: ");
        int choice = sc.nextInt();
        sc.nextLine();
        switch (choice) {
            case 1:
                Students s = new Students("", 0, "", "");
                s.getStudentDetails();
                s.displayStudentDetails();
                break;
            case 2:
                Faculty f = new Faculty("", "", "");
                f.getFacultyDetails();
                f.displayFacultyDetails();
                break;
            default:
               System.out.println("Invalid Choice");
        }

        sc.close();
    }
}