#include<stdio.h>
#include<string.h>
#include<stdlib.h>
#include<math.h>

#define Employee struct emp

void add(FILE * fp);
FILE * del(FILE * fp);
void modify(FILE * fp);
void displayList(FILE * fp);
void searchRecord(FILE *fp);
void printChar(char ch,int n);
void printHead();

struct emp
{
    int id;
    char name[100];
    char desgn[10];
    float sal;
    char jdate[8];
    char gender[10];
    char branch[50];
    char psaddr[200];
    char prtaddr[200];
    char phone[15];
    char mail[20];
};

int main()
{
    FILE * fp;
    Employee e;
    int option;
    char another;
    
    if((fp=fopen("employeeInfo.txt","rb+"))==NULL)
    {
        if((fp=fopen("employeeInfo.txt","wb+"))==NULL)
        {
            printf("can't open file");
            return 0;
        }
    }
    
    char username[10],password[10];
    printHead();
    printf("\n\t\t\t\t  Login Screen");
    printf("\n\t\t\t      Enter Your Credential");
    printf("\n\n\n\t\tUsername: ");
    scanf("%s",username);
    printf("\n\t\tPassword: ");
    scanf("%s",password);
    
    if(((strcasecmp(username,"admin"))==0)&&((strcasecmp(password,"pass")==0)))
    {
        while(1)
        {
            printHead();
            printf("\n\t\t\t\tMain Menu");
            printf("\n\n\n");
            
            printf("\n\n\t\t\t1. Add Employee");
            printf("\n\n\t\t\t2. Delete Employee");
            printf("\n\n\t\t\t3. Modify Employee");
            printf("\n\n\t\t\t4. Display Employee List");
            printf("\n\n\t\t\t5. Search Record");
            printf("\n\n\t\t\t0. EXIT");
            
            printf("\n\n\t\tEnter Your Option :--> ");
            scanf("%d",&option);
            
            switch(option)
            {
                case 0: 
                    return 1;
                    break;
                case 1: 
                    add(fp);
                    break;
                case 2: 
                    fp=del(fp);
                    break;
                case 3: 
                    modify(fp);
                    break;
                case 4: 
                    displayList(fp);
                    break;
                case 5: 
                    searchRecord(fp);
                    break;
                default: 
                    printf("\n\t\tYou Pressed wrong key");
                    printf("\n\t\tProgram terminated");
                    exit(0);
            }
        }
    }
    else {
        printf("\n\t\tLogin Failed");
    }
    
    return 1;
}

void printChar(char ch,int n)
{
    while(n--)
    {
        putchar(ch);
    }
}

void printHead()
{
    system("cls");
    printf("\t");
    printChar('=',65);
    printf("\n\t");
    printChar('=',16);
    printf("[EMPLOYEE] [MANAGEMENT] [SYSTEM]");
    printChar('=',16);
    printf("\n\t");
    printChar('=',65);
}

void add(FILE * fp)
{
    printHead();
    printf("\n\t\t\t\Add Employee");
    char another='y';
    Employee e;
    
    fseek(fp,0,SEEK_END);
    while(another=='y'||another=='Y')
    {
        printf("\n\n\t\tEnter ID number: ");
        scanf("%d",&e.id);
        
        printf("\n\n\t\tEnter Full Name of Employee: ");
        fflush(stdin);
        fgets(e.name,100,stdin);
        e.name[strlen(e.name)-1]='\0';
        
        printf("\n\n\t\tEnter Designation: ");
        fflush(stdin);
        fgets(e.desgn,10,stdin);
        e.desgn[strlen(e.desgn)-1]='\0';
        
        printf("\n\n\t\tEnter Gender: ");
        fflush(stdin);
        fgets(e.gender,10,stdin);
        e.gender[strlen(e.gender)-1]='\0';
        
        printf("\n\n\t\tEnter Branch: ");
        fflush(stdin);
        fgets(e.branch,50,stdin);
        e.branch[strlen(e.branch)-1]='\0';
        
        printf("\n\n\t\tEnter Salary: ");
        scanf("%f",&e.sal);
        
        fwrite(&e,sizeof(e),1,fp);
        
        printf("\n\n\t\tWant to enter another employee info (Y/N)\t");
        fflush(stdin);
        another=getchar();
    }
}

FILE * del(FILE * fp)
{
    printHead();
    printf("\n\t\t\t\Delete Employee");
    Employee e;
    int flag=0,tempid,siz=sizeof(e);
    FILE *ft;
    
    if((ft=fopen("temp.txt","wb+"))==NULL)
    {
        printf("\n\n\t\t\t\\t!!! ERROR !!!\n\t\t");
        return fp;
    }
    
    printf("\n\n\tEnter ID number of Employee to Delete the Record");
    printf("\n\n\t\t\tID No. : ");
    scanf("%d",&tempid);
    
    rewind(fp);
    
    while((fread(&e,siz,1,fp))==1)
    {
        if(e.id==tempid)
        { 
            flag=1;
            printf("\n\tRecord Deleted for");
            printf("\n\n\t\t%s\n\n\t\t%s\n\n\t\t%d\n\t",e.name,e.branch,e.id);
            continue;
        }
        fwrite(&e,siz,1,ft);
    }
    
    fclose(fp);
    fclose(ft);
    
    remove("employeeInfo.txt");
    rename("temp.txt","employeeInfo.txt");
    
    if((fp=fopen("employeeInfo.txt","rb+"))==NULL)
    {
        printf("ERROR");
        return NULL;
    }
    
    if(flag==0) 
        printf("\n\n\t\t!!!! ERROR RECORD NOT FOUND \n\t");
    
    return fp;
}

void modify(FILE * fp)
{
    printHead();
    printf("\n\t\t\t\Modify Employee");
    Employee e;
    int i,flag=0,tempid,siz=sizeof(e);
    
    printf("\n\n\tEnter ID Number of Employee to Modify the Record : ");
    scanf("%d",&tempid);
    
    rewind(fp);
    
    while((fread(&e,siz,1,fp))==1)
    {
        if(e.id==tempid)
        {
            flag=1;
            break;
        }
    }
    
    if(flag==1)
    {
        fseek(fp,-siz,SEEK_CUR);
        printf("\n\n\t\tRecord Found");
        printf("\n\n\t\tEnter New Data for the Record");
        
        printf("\n\n\t\tEnter ID number: ");
        scanf("%d",&e.id);
        
        printf("\n\n\t\tEnter Full Name of Employee: ");
        fflush(stdin);
        fgets(e.name,100,stdin);
        e.name[strlen(e.name)-1]='\0';
        
        printf("\n\n\t\tEnter Designation: ");
        fflush(stdin);
        fgets(e.desgn,10,stdin);
        e.desgn[strlen(e.desgn)-1]='\0';
        
        printf("\n\n\t\tEnter Gender: ");
        fflush(stdin);
        fgets(e.gender,10,stdin);
        e.gender[strlen(e.gender)-1]='\0';
        
        printf("\n\n\t\tEnter Branch: ");
        fflush(stdin);
        fgets(e.branch,50,stdin);
        e.branch[strlen(e.branch)-1]='\0';
        
        printf("\n\n\t\tEnter Salary: ");
        scanf("%f",&e.sal);
        
        fwrite(&e,sizeof(e),1,fp);
    }
    else 
        printf("\n\n\t!!!! ERROR !!!! RECORD NOT FOUND");
}

void displayList(FILE * fp)
{   
    printHead();
    printf("\n\t\t\t\List of Employees");
    Employee e;
    int i,siz=sizeof(e);
    
    rewind(fp);
    
    while((fread(&e,siz,1,fp))==1)
    {
        printf("\n\n\t\tID : %d",e.id);
        printf("\n\n\t\tNAME : %s",e.name);
        printf("\n\n\t\tDESIGNATION : %s",e.desgn);
        printf("\n\n\t\tGENDER : %s",e.gender);
        printf("\n\n\t\tBRANCH : %s",e.branch);
        printf("\n\n\t\tSALARY : %.2f",e.sal);
        printChar('=',65);
    }
}

void searchRecord(FILE *fp)
{
    printHead();
    printf("\n\t\t\t\Search Employee");
    int tempid,flag,siz,i;
    Employee e;
    char another='y';
    
    siz=sizeof(e);
    
    while(another=='y'||another=='Y')
    {
        printf("\n\n\tEnter ID Number of Employee to search the record : ");
        scanf("%d",&tempid);
        
        rewind(fp);
        
        while((fread(&e,siz,1,fp))==1)
        {
            if(e.id==tempid)
            {
                flag=1;
                break;
            }
        }
        
        if(flag==1)
        {
            printf("\n\t\tNAME : %s",e.name);
            printf("\n\n\t\tID : %d",e.id);
            printf("\n\n\t\tDESIGNATION : %s",e.desgn);
            printf("\n\n\t\tBRANCH : %s",e.branch);
            printf("\n\n\t\tSALARY: %.2f",e.sal);
            printChar('=',65);
        }
        else
            printf("\n\n\t\t!!!! ERROR RECORD NOT FOUND !!!!");
        
        printf("\n\n\t\tWant to enter another search (Y/N)");
        fflush(stdin);
        another=getchar();
    }
}