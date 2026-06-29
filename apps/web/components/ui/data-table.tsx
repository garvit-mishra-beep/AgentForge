import * as React from "react";

interface DataTableColumn<T> {
  accessorKey: keyof T;
  header: string;
  cell?: (data: T) => React.ReactNode;
  sortable?: boolean;
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  data: T[];
  className?: string;
}

export function DataTable<T>({
  columns,
  data,
  className,
}: DataTableProps<T>) {
  if (data.length === 0) {
    return (
      <div className={className}>
        <p className="text-center py-4 text-muted-foreground">
          No data found.
        </p>
      </div>
    );
  }

  return (
    <div className={className}>
      <table className="w-full text-left border-collapse">
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.accessorKey as string}
                className="border-b font-semibold text-muted-foreground px-4 py-3 text-left"
                onClick={column.sortable ? () => {} : undefined}
              >
                {column.header}
                {column.sortable && (
                  <span className="ml-1 h-4 w-4 inline-block opacity-50">
                    {/* Sort indicator would go here */}
                  </span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-muted">
          {data.map((row, rowIndex) => (
            <tr
              key={rowIndex}
              className="hover:bg-muted/50"
            >
              {columns.map((column, colIndex) => (
                <td
                  key={`${rowIndex}-${colIndex}`}
                  className="px-4 py-3 whitespace-nowrap"
                >
                  {column.cell ? column.cell(row) : String(row[column.accessorKey])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
